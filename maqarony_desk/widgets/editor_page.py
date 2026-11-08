# MaqaronyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
"""One lazily-created editor page for a Markdown document.

Responsibilities:
- load and save a single file
- synchronize Qt's native modified flag with ModuleRepository
- provide Find, Replace, and Go to Line controls
- detect external file changes without silently discarding edits
- expose external-editor, rename, duplicate, and remove signals

The page does not rename or delete files itself. Those actions belong to the
file controller, keeping this widget focused and testable.
"""

from __future__ import annotations

from html import escape
import codecs
import locale
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDropEvent,
    QColor,
    QFont,
    QFontDatabase,
    QKeySequence,
    QPalette,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFontDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from maqarony_desk.widgets.message_conventions import (
    DEFAULT_MESSAGE_DURATION_MS, is_critical_status, status_sentence,
)
from maqarony_desk.widgets.mwpyn.character_count import count_markdown_characters

class EditorMessageStatusBar(QStatusBar):
    """Keep editor feedback at left without hiding document indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_label = QLabel("", self)
        self.message_label.setMinimumWidth(0)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.message_label.setToolTip("")
        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self.clearMessage)

    def showMessage(self, message, timeout=DEFAULT_MESSAGE_DURATION_MS, *, warning_id=None):
        text = status_sentence(message)
        critical = is_critical_status(text)
        recovering = text.startswith(("Loaded ", "Saved ", "Saved as ", "Saved MaqaronyDesk version as "))
        if getattr(self, "_critical_editor_message", False) and not (critical or recovering):
            return
        self._critical_editor_message = critical
        self._warning_id = warning_id if critical else None
        if critical:
            timeout = 0
        self.message_label.setText(text)
        self.message_label.setToolTip(text)
        self._message_timer.stop()
        if int(timeout) > 0:
            self._message_timer.start(int(timeout))

    def clearMessage(self, *, warning_id=None):
        if warning_id is not None and getattr(self, "_warning_id", None) != warning_id:
            return
        self._message_timer.stop()
        self._critical_editor_message = False
        self._warning_id = None
        self.message_label.clear()
        self.message_label.setToolTip("")


from maqarony_desk.app_constants import MARKDOWN_EXTENSIONS
from maqarony_desk.legacy_ricopad import strip_legacy_envelope
from maqarony_desk.models.module import Module
from maqarony_desk.models.module_repository import ModuleRepository
from maqarony_desk.widgets.code_editor import CodeEditor
from maqarony_desk.widgets.mwpyn.editor_preview import MarkdownPreview
from maqarony_desk.services.config_service import ConfigService
from maqarony_desk.services.file_io import (
    FileSnapshot,
    FileStateChangedError,
    FileTooLargeError,
    UnsupportedFileError,
    current_file_state,
    fsync_directory,
    install_new_file_from_temp,
    read_regular_file,
    snapshot_from_payload,
    validated_symlink_target,
)


def _host_process_environment() -> dict[str, str]:
    """Return a clean host environment for More Symbols utilities."""
    environment = os.environ.copy()
    if sys.platform == "win32":
        return environment
    if not (environment.get("APPDIR") or getattr(sys, "frozen", False)):
        return environment
    appdir = environment.get("APPDIR")
    original_library_path = environment.pop("LD_LIBRARY_PATH_ORIG", None)
    if original_library_path is None:
        environment.pop("LD_LIBRARY_PATH", None)
    else:
        environment["LD_LIBRARY_PATH"] = original_library_path
    for variable in (
        "APPDIR", "APPIMAGE", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM",
        "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORMTHEME",
        "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH",
    ):
        environment.pop(variable, None)
    if appdir and environment.get("PATH"):
        appdir_real = os.path.realpath(appdir)
        clean_path: list[str] = []
        for entry in environment["PATH"].split(os.pathsep):
            if not entry:
                continue
            try:
                entry_real = os.path.realpath(entry)
                inside = os.path.commonpath((appdir_real, entry_real)) == appdir_real
            except (OSError, ValueError):
                inside = False
            if not inside:
                clean_path.append(entry)
        environment["PATH"] = os.pathsep.join(clean_path)
    return environment


from maqarony_desk.widgets.editor_lifecycle import EditorLifecycleMixin
from maqarony_desk.widgets.editor_page_search_view import EditorPageSearchViewMixin
from maqarony_desk.widgets.editor_page_printing import EditorPagePrintingMixin
from maqarony_desk.widgets.editor_page_preferences import EditorPagePreferencesMixin
from maqarony_desk.widgets.editor_page_commands_appearance import EditorPageCommandsAppearanceMixin
class EditorPage(EditorLifecycleMixin, EditorPageCommandsAppearanceMixin, EditorPagePreferencesMixin, EditorPagePrintingMixin, EditorPageSearchViewMixin, QWidget):
    """Editor and file controls for one repository Module."""

    MAX_FILE_BYTES = 25 * 1024 * 1024
    MAX_SEARCH_QUERY_CHARACTERS = 4096
    MAX_SEARCH_MATCHES = 10_000

    external_editor_requested = pyqtSignal(object)
    containing_folder_requested = pyqtSignal(object)
    rename_requested = pyqtSignal(object)
    remove_requested = pyqtSignal(object)
    duplicate_requested = pyqtSignal(object)
    undo_redo_changed = pyqtSignal(bool, bool)
    status_message = pyqtSignal(str)
    saved = pyqtSignal(object)
    preferences_changed = pyqtSignal()
    external_files_dropped = pyqtSignal(object, object)
    view_mode_changed = pyqtSignal(str)
    path_changed = pyqtSignal(object, object, object)

    def __init__(
        self,
        module: Module,
        repository: ModuleRepository,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.module = module
        self.repository = repository
        self.config = config
        self.editor = CodeEditor(self)
        self.preview = MarkdownPreview(self)
        self.preview.setAcceptDrops(False)
        self.view_mode = str(self.config.get("markopad_view_mode", "split"))
        if self.view_mode not in {"source", "split", "preview"}:
            self.view_mode = "split"
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self.refresh_preview_now)
        self.view_only = bool(self.config.get("lock_editor", False))
        self._view_only_notice_shown = False
        self.file_encoding = "utf-8"
        self.file_bom = b""
        self.file_newline = "\n"
        self.file_disk_snapshot: FileSnapshot | None = None
        self.legacy_ricopad_loaded = False
        stored_split = self.config.get_int_list(
            "markopad_editor_splitter_sizes", [3, 2], length=2
        )
        self._last_splitter_sizes = (
            stored_split if len(stored_split) == 2 and all(value > 0 for value in stored_split)
            else [3, 2]
        )
        self._header_visible = bool(config.get("show_file_header", True))

        self._loaded_mtime_ns: int | None = None
        self._external_change_pending = False
        self._backing_state = "normal"
        self._cached_status_char_count = None
        self._ignore_document_signal = False
        self._last_find_text = ""
        self._search_matches: list[tuple[int, int]] = []
        self._current_search_index = -1
        self._search_results_truncated = False
        self._search_refresh_suspended = False

        self._build_ui()
        self._connect_signals()
        self.loaded_successfully = self.load_from_disk(show_errors=False)
        self._refresh_header()

    def _build_ui(self) -> None:
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(0)
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        page_layout.addLayout(root, 1)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setVisible(self._header_visible)
        root.addWidget(self.title_label)

        self.external_banner = QFrame()
        self.external_banner.setFrameShape(QFrame.Shape.StyledPanel)
        banner_layout = QHBoxLayout(self.external_banner)
        self.external_label = QLabel("This file changed on disk after it was opened.")
        self.external_label.setWordWrap(True)
        banner_layout.addWidget(self.external_label, 1)
        self.reload_external_button = QPushButton("Reload from Disk")
        self.reload_external_button.clicked.connect(self._reload_external_change)
        save_version = QPushButton("Save Version As…")
        save_version.clicked.connect(self._save_editor_version_as)
        banner_layout.addWidget(self.reload_external_button)
        banner_layout.addWidget(save_version)
        self.external_banner.hide()
        root.addWidget(self.external_banner)

        # Keep the Sheepy-derived editor actions internally available for
        # state synchronization; the application-global menu bar is the only
        # visible editor command menu surface.
        self._build_editor_menus()

        # MaqaronyDesk keeps the established document page shell and uses MaqaronyPad's
        # canonical Source / Source + Preview / Preview document surface.
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.content_splitter.addWidget(self.editor)
        self.content_splitter.addWidget(self.preview)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setSizes(self._last_splitter_sizes)
        root.addWidget(self.content_splitter, 1)

        # MaqaronyPad's authoritative two-row Find/Replace panel lives at the
        # bottom of the editor surface. Plus keeps the newer bounded/safe
        # search engine underneath without changing this interaction model.
        self.search_frame = QFrame(self)
        self.search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_grid = QGridLayout(self.search_frame)
        search_grid.setContentsMargins(8, 6, 8, 6)
        self.find_input = QLineEdit(self.search_frame)
        self.find_input.setMaxLength(self.MAX_SEARCH_QUERY_CHARACTERS)
        self.find_input.setPlaceholderText("Find")
        self.replace_input = QLineEdit(self.search_frame)
        self.replace_input.setPlaceholderText("Replace")
        self.search_case_checkbox = QCheckBox("Match case", self.search_frame)
        self.search_counter = QLabel("", self.search_frame)
        self.search_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_previous_button = QPushButton("Previous", self.search_frame)
        self.search_next_button = QPushButton("Next", self.search_frame)
        replace_button = QPushButton("Replace", self.search_frame)
        replace_all_button = QPushButton("Replace All", self.search_frame)
        close_search = QPushButton("Close", self.search_frame)
        search_grid.addWidget(self.find_input, 0, 0, 1, 3)
        search_grid.addWidget(self.search_previous_button, 0, 3)
        search_grid.addWidget(self.search_next_button, 0, 4)
        search_grid.addWidget(self.search_case_checkbox, 0, 5)
        search_grid.addWidget(self.search_counter, 0, 6)
        search_grid.addWidget(self.replace_input, 1, 0, 1, 3)
        search_grid.addWidget(replace_button, 1, 3)
        search_grid.addWidget(replace_all_button, 1, 4)
        search_grid.addWidget(close_search, 1, 6)
        self.find_input.textChanged.connect(self.refresh_search)
        self.search_case_checkbox.toggled.connect(self.refresh_search)
        self.find_input.returnPressed.connect(self.find_next)
        self.search_previous_button.clicked.connect(self.find_previous)
        self.search_next_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_current)
        replace_all_button.clicked.connect(self.replace_all)
        close_search.clicked.connect(self.hide_find_panel)
        # Compatibility aliases keep the hardened Plus replace implementation
        # attached to the MaqaronyPad panel fields rather than a separate dialog.
        self.replace_find_entry = self.find_input
        self.replace_with_entry = self.replace_input
        self.replace_case_checkbox = self.search_case_checkbox
        self.search_frame.hide()
        root.addWidget(self.search_frame)

        self.editor_status = EditorMessageStatusBar(self)
        self.editor_status.setSizeGripEnabled(False)
        self.status_indicators_label = QLabel("", self.editor_status)
        self.status_indicators_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_indicators_label.setMinimumWidth(0)
        self.editor_status.addWidget(self.editor_status.message_label, 1)
        self.editor_status.addPermanentWidget(self.status_indicators_label)
        page_layout.addWidget(self.editor_status, 0)

        self.apply_preferences()




    @staticmethod
    def _dropped_markdown_paths(mime_data) -> list[Path]:
        if not mime_data.hasUrls():
            return []
        paths: list[Path] = []
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile()).expanduser().resolve(strict=False)
            if path.is_file() and path.suffix.casefold() in MARKDOWN_EXTENSIONS:
                paths.append(path)
        return paths

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_markdown_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._dropped_markdown_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._dropped_markdown_paths(event.mimeData())
        if paths:
            self.external_files_dropped.emit(paths, self.module.path.parent)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _connect_signals(self) -> None:
        self.editor.document().modificationChanged.connect(self._on_modification_changed)
        self.editor.document().undoAvailable.connect(self._emit_undo_redo_state)
        self.editor.document().redoAvailable.connect(self._emit_undo_redo_state)
        # Bind editor feedback before the constructor loads the first document.
        self.status_message.connect(self.show_editor_status)
        self.editor.paste_rejected.connect(self.status_message)
        self.preview.missing_link_requested.connect(
            lambda: self.show_editor_status("The linked file could not be found.", 4000)
        )
        self.editor.go_to_line_requested.connect(self.show_go_to_line)
        self.editor.view_only_edit_attempt.connect(self.show_view_only_edit_prompt)
        self.editor.overwrite_mode_changed.connect(self._update_operation_mode)
        self.editor.files_dropped.connect(
            lambda paths: self.external_files_dropped.emit(paths, self.module.path.parent)
        )
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)
        self.editor.textChanged.connect(self._invalidate_status_char_count)
        self.editor.textChanged.connect(self._update_cursor_position)
        self.editor.textChanged.connect(self.schedule_preview)
        self.editor.textChanged.connect(
            lambda: (
                None if self._search_refresh_suspended
                else self.refresh_search() if self.search_frame.isVisible()
                else self.clear_search_results()
            )
        )
        self.repository.module_changed.connect(self._on_repository_module_changed)
        self.repository.module_path_changed.connect(self._on_module_path_changed)
        self.content_splitter.splitterMoved.connect(self._remember_splitter_sizes)

    def _emit_undo_redo_state(self, *_args) -> None:
        document = self.editor.document()
        undo_available = document.isUndoAvailable() and not self.view_only
        redo_available = document.isRedoAvailable() and not self.view_only
        self.undo_action.setEnabled(undo_available)
        self.redo_action.setEnabled(redo_available)
        self.undo_redo_changed.emit(undo_available, redo_available)

    def _apply_presentation_safely(self, callback) -> None:
        """Run presentation-only work without changing document dirty state."""
        document = self.editor.document()
        was_modified = bool(document.isModified())
        previous_ignore = self._ignore_document_signal
        self._ignore_document_signal = True
        try:
            callback()
            if bool(document.isModified()) != was_modified:
                document.setModified(was_modified)
        finally:
            self._ignore_document_signal = previous_ignore
        # The repository is authoritative for the Plus dirty indicator; keep it
        # synchronized with the exact state that existed before presentation work.
        self.repository.set_dirty(self.module.path, was_modified)
        self._refresh_header()





    def show_editor_status(
        self, message: str, timeout: int = DEFAULT_MESSAGE_DURATION_MS,
        *, warning_id: str | None = None,
    ) -> None:
        """Show feedback in this document's editor status bar."""
        self.editor_status.showMessage(
            str(message), max(0, int(timeout)), warning_id=warning_id
        )


    def reset_content_splitter(self) -> None:
        """Restore and persist the canonical 3:2 Source/Preview split."""
        if self.view_mode != "split":
            return
        self._last_splitter_sizes = [3, 2]
        self.content_splitter.setSizes([3, 2])
        sizes = [int(value) for value in self.content_splitter.sizes()]
        if len(sizes) == 2 and all(value > 0 for value in sizes):
            self._last_splitter_sizes = sizes
        self.config.set(
            "markopad_editor_splitter_sizes",
            list(self._last_splitter_sizes),
            save=True,
        )

    def _remember_splitter_sizes(self, *_args) -> None:
        """Remember the Source/Preview split without confusing it with the app sidebar splitter."""
        if self.view_mode != "split":
            return
        sizes = [int(value) for value in self.content_splitter.sizes()]
        if len(sizes) != 2 or not all(value > 0 for value in sizes):
            return
        self._last_splitter_sizes = sizes
        self.config.set("markopad_editor_splitter_sizes", list(sizes), save=False)


    def schedule_preview(self) -> None:
        if self.preview.isVisible():
            self.preview_timer.start()

    def refresh_preview_now(self, *, force: bool = False) -> None:
        if force or self.preview.isVisible():
            self.preview.render_markdown(self.editor.toPlainText())
            self._apply_preview_link_color()
            self._apply_preview_quote_effect()








    def _insert_curated_symbol(self, symbol: str, dialog: QDialog | None = None) -> None:
        if self.view_only or self.editor.isReadOnly() or self.view_mode == "preview":
            self.show_view_only_edit_prompt() if self.view_only else None
            if dialog is not None:
                dialog.reject()
            return
        if self.editor.insert_guarded_text(symbol):
            if dialog is not None:
                dialog.accept()
            self.editor.setFocus()
            self.editor.ensureCursorVisible()

    def _open_more_symbols(self, dialog: QDialog | None = None) -> None:
        if dialog is not None:
            dialog.accept()
        if sys.platform == "win32":
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            candidates = (
                os.path.join(system_root, "System32", "charmap.exe"),
                "charmap.exe",
            )
            missing = "Windows Character Map could not be found on this system."
        else:
            candidates = ("kcharselect", "gucharmap", "gnome-characters", "charmap")
            missing = (
                "No supported character-map application was found.\n\n"
                "Install KCharSelect, GNOME Characters, or Gucharmap to use this option."
            )
        host_environment = _host_process_environment()
        host_path = host_environment.get("PATH")
        for command in candidates:
            executable = command if os.path.isfile(command) else shutil.which(command, path=host_path)
            if not executable:
                continue
            try:
                subprocess.Popen(
                    [executable],
                    env=host_environment,
                    start_new_session=(sys.platform != "win32"),
                )
                self.editor.setFocus()
                return
            except OSError:
                continue
        QMessageBox.information(self, "More Symbols", missing)
        self.editor.setFocus()

    def show_symbols_dialog(self) -> None:
        """Show the common Plus curated symbol grid using Marko insertion safety."""
        if self.view_only or self.editor.isReadOnly() or self.view_mode == "preview":
            if self.view_only:
                self.show_view_only_edit_prompt()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Symbols")
        dialog.setModal(True)
        layout = QGridLayout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(5)
        symbols = (
            "©", "®", "™", "°", "•", "·", "—", "–",
            "…", "→", "←", "↑", "↓", "✓", "✗", "§",
            "£", "€", "$", "¥", "¢", "±", "×", "÷",
            "≠", "≤", "≥", "≈", "∞", "µ", "¶", "№",
            "★", "☆", "♥", "♦", "♣", "♠", "☐", "☑",
        )
        columns = 8
        for index, symbol in enumerate(symbols):
            button = QToolButton(dialog)
            button.setText(symbol)
            button.setToolTip(f"Insert {symbol}")
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(34, 30)
            button.clicked.connect(
                lambda _checked=False, value=symbol: self._insert_curated_symbol(value, dialog)
            )
            layout.addWidget(button, index // columns, index % columns)
        row = (len(symbols) + columns - 1) // columns
        separator = QFrame(dialog)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator, row, 0, 1, columns)
        more_button = QPushButton("More Symbols…", dialog)
        more_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        more_button.clicked.connect(lambda _checked=False: self._open_more_symbols(dialog))
        layout.addWidget(more_button, row + 1, 0, 1, columns)
        dialog.adjustSize()
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            dialog.move(
                geometry.center().x() - dialog.width() // 2,
                geometry.center().y() - dialog.height() // 2,
            )
        dialog.exec()
        self.editor.setFocus()



    def choose_display_font(self) -> None:
        selected, accepted = QFontDialog.getFont(self.editor.font(), self, "Display Font")
        if not accepted:
            return
        self.config.update({
            "editor_font_family": selected.family(),
            "editor_font_size": selected.pointSize(),
            "editor_font_weight": int(selected.weight()),
            "editor_font_italic": selected.italic(),
        }, save=True)
        self.preferences_changed.emit()

    def preview_base_font(self) -> QFont:
        """Return MaqaronyPad's application-based persisted Preview font."""
        font = QFont(QApplication.font())
        stored = self.config.get("preview_font", "")
        if isinstance(stored, str) and stored:
            candidate = QFont()
            if candidate.fromString(stored):
                font = candidate
        if font.pointSizeF() <= 0:
            font.setPointSizeF(10.0)
        return font

    def apply_preview_font(self) -> None:
        font = self.preview_base_font()
        zoom_percent = self.config.get_int("markopad_zoom", 100, minimum=50, maximum=300)
        font.setPointSizeF(max(6.0, font.pointSizeF() * zoom_percent / 100.0))
        self.preview.document().setDefaultFont(font)

    def choose_preview_font(self) -> None:
        dialog = QFontDialog(self.preview_base_font(), self)
        dialog.setWindowTitle("Preview Font — MaqaronyDesk")
        dialog.setOption(
            QFontDialog.FontDialogOption.DontUseNativeDialog,
            True,
        )

        effects = next(
            (
                group
                for group in dialog.findChildren(QGroupBox)
                if group.title().replace("&", "").strip().casefold() == "effects"
            ),
            None,
        )
        if effects is None or effects.layout() is None:
            return

        effects_layout = effects.layout()
        italic_quotes = QCheckBox("Italicize block quotations", effects)
        italic_quotes.setChecked(
            bool(self.config.get("preview_italic_quotes", False))
        )
        if isinstance(effects_layout, QGridLayout):
            effects_layout.addWidget(
                italic_quotes,
                effects_layout.rowCount(),
                0,
                1,
                max(1, effects_layout.columnCount()),
            )
        else:
            effects_layout.addWidget(italic_quotes)

        def update_effect_availability(font: QFont) -> None:
            already_italic = font.italic()
            italic_quotes.setEnabled(not already_italic)
            italic_quotes.setToolTip(
                "The selected Preview font is already italic."
                if already_italic
                else ""
            )

        dialog.currentFontChanged.connect(update_effect_availability)
        update_effect_availability(dialog.currentFont())

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dialog.currentFont()
        self.config.update({
            "preview_font": selected.toString(),
            "preview_italic_quotes": italic_quotes.isChecked(),
        }, save=True)
        self.apply_preview_font()
        self.refresh_preview_now(force=True)
        self.preferences_changed.emit()


    def toggle_view_only(self, checked: bool) -> None:
        requested = bool(checked)
        should_confirm = bool(self.config.get("confirm_locked_mode_disable", True))
        if self.view_only and not requested and should_confirm:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Disable Locked Mode? — MaqaronyDesk")
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText("Locked Mode protects files from accidental changes.")
            dialog.setInformativeText(
                "Continue only when you intend to edit the document."
            )
            dont_ask = QCheckBox(
                "Don't ask again when disabling Locked Mode", dialog
            )
            dialog.setCheckBox(dont_ask)
            keep = dialog.addButton(
                "Keep Locked", QMessageBox.ButtonRole.RejectRole
            )
            cont = dialog.addButton(
                "Continue", QMessageBox.ButtonRole.AcceptRole
            )
            dialog.setDefaultButton(keep)
            dialog.setEscapeButton(keep)
            dialog.exec()
            if dialog.clickedButton() is not cont:
                self.view_only_action.blockSignals(True)
                self.view_only_action.setChecked(True)
                self.view_only_action.blockSignals(False)
                return
            if dont_ask.isChecked():
                self.config.set(
                    "confirm_locked_mode_disable", False, save=True
                )
        self.set_view_only(requested)
        message = "Locked Mode enabled." if requested else "Locked Mode disabled."
        self.editor_status.showMessage(message, 4000)


    def set_view_only(self, enabled: bool) -> None:
        enabled = bool(enabled)
        self.view_only = enabled
        self._view_only_notice_shown = False
        self.view_only_action.blockSignals(True)
        self.view_only_action.setChecked(enabled)
        self.view_only_action.blockSignals(False)
        self.editor.set_view_only(enabled)
        for action in (self.undo_action, self.redo_action, self.cut_action, self.paste_plain_action, self.delete_action, self.comment_action, self.duplicate_line_action, self.replace_action, self.replace_all_action):
            action.setEnabled(not enabled)
        self._emit_undo_redo_state()

    def show_view_only_edit_prompt(self) -> None:
        message = "Editing is disabled while Locked Mode is enabled."
        self.editor_status.showMessage(message, 4000)
        if self._view_only_notice_shown:
            return
        self._view_only_notice_shown = True
        QMessageBox.information(
            self,
            "Locked Mode — MaqaronyDesk",
            "Editing is disabled because Locked Mode is enabled.\n\n"
            "Clear View → Locked Mode and confirm Continue to edit the document.",
        )

    def _update_operation_mode(self, overwrite: bool) -> None:
        self._update_cursor_position()
        self.show_editor_status(
            "Overwrite mode enabled." if overwrite else "Insert mode enabled.", 4000
        )

    def _invalidate_status_char_count(self) -> None:
        """Invalidate only the cached document total after a text edit."""
        self._cached_status_char_count = None

    def _update_cursor_position(self) -> None:
        cursor = self.editor.textCursor()
        total_chars = self._cached_status_char_count
        if total_chars is None:
            total_chars = count_markdown_characters(self.editor.document())
            self._cached_status_char_count = total_chars
        document_text = (
            f"Ln {cursor.blockNumber() + 1}/{self.editor.blockCount()} "
            f"Col {cursor.positionInBlock() + 1} Chars {total_chars:,}"
        )
        mode = "Overwrite" if self.editor.overwriteMode() else "Insert"
        view = {"source": "Source", "split": "Split", "preview": "Preview"}.get(self.view_mode, "Split")
        zoom = self.config.get_int("markopad_zoom", 100, minimum=50, maximum=300)
        newline = {"\n": "LF", "\r\n": "CRLF", "\r": "CR"}.get(self.file_newline, "LF")
        indicators = f"{mode} · {document_text} · {self.file_encoding.upper()} {newline} · {view} {zoom}%"
        self.status_indicators_label.setText(indicators)
        self.status_indicators_label.setToolTip(indicators)







































    def set_header_visible(self, visible: bool) -> None:
        self._header_visible = bool(visible)
        self.title_label.setVisible(self._header_visible)

    def _refresh_header(self) -> None:
        dirty = " [Unsaved]" if self.module.dirty else ""
        display_name = escape(self.module.display_name)
        path_text = escape(str(self.module.path))
        self.title_label.setText(
            f"<h2>{display_name}{dirty}</h2>"
            f"{path_text}"
        )
