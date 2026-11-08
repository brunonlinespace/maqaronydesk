# MaqaronyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application window for MaqaronyDesk."""

from __future__ import annotations

import json
import os
import sys
import time
import subprocess
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QEvent, QTimer, Qt, QUrl
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QIcon,
    QKeySequence,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QSpinBox,
    QTabBar,
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QWidget,
)

from maqarony_desk import APP_NAME
from maqarony_desk.app_constants import (
    GITHUB_URL,
    ISSUES_URL,
    MARKDOWN_EXTENSIONS,
)
from maqarony_desk.controllers.editor_manager import EditorManager
from maqarony_desk.controllers.file_actions import FileActionsController
from maqarony_desk.models.module import Module
from maqarony_desk.models.module_repository import ModuleRepository
from maqarony_desk.models.module_state_store import ModuleStateStore
from maqarony_desk.services.config_service import ConfigService
from maqarony_desk.services.filesystem_watcher import FilesystemWatcher
from maqarony_desk.services.desktop_launcher import DesktopLauncher
from maqarony_desk.services.project_registry import ProjectRegistry
from maqarony_desk.services.runtime_paths import RuntimePaths
from maqarony_desk.widgets.dialogs.about_dialog import AboutDialog
from maqarony_desk.widgets.dialogs.closing_dialog import ClosingDialog
from maqarony_desk.widgets.editor_page import EditorPage
from maqarony_desk.widgets.workspace.navigation import (
    NavigationWidget,
    SIDEBAR_MINIMUM_WIDTH,
)
from maqarony_desk.widgets.dialogs.projects_dialog import ProjectsDialog
from maqarony_desk.widgets.dialogs.shortcuts_dialog import ShortcutsDialog
from maqarony_desk.widgets.shell_ribbon import ShellRibbon
from maqarony_desk.widgets.window_parts.document_tabs import DocumentTabsMixin
from maqarony_desk.widgets.window_parts.navigation_history import NavigationHistoryMixin
from maqarony_desk.widgets.window_parts.layout_controls import LayoutControlsMixin
from maqarony_desk.widgets.window_parts.help_actions import HelpActionsMixin
from maqarony_desk.widgets.theme import apply_theme, effective_scheme


SHUTDOWN_PROFILE_ENV = "MAQARONYDESK_PROFILE_SHUTDOWN"


from maqarony_desk.widgets.editor_printing import EditorPrintingMixin
from maqarony_desk.widgets.editor_commands_appearance import EditorCommandsAppearanceMixin
class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):
    """Assembles the repository, services, controllers, and persistent views."""

    def __init__(
        self,
        library_root: str | Path,
        config: ConfigService,
        project_registry: ProjectRegistry,
        runtime_paths: RuntimePaths,
        parent=None,
        *,
        icon_path: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.library_root = Path(library_root).expanduser().resolve(strict=False)
        self.config = config
        self.icon_family = str(self.config.get("app_icon_family", "harmony"))
        if self.icon_family not in {"harmony", "humility", "heritage", "halcyon"}:
            self.icon_family = "harmony"
        QApplication.instance().setProperty("maqa_icon_family", self.icon_family)
        self.project_registry = project_registry
        self.runtime_paths = runtime_paths

        self.package_root = Path(__file__).resolve().parent.parent
        self.project_root = self.package_root.parent
        self.icon_path = (
            Path(icon_path)
            if icon_path is not None
            else self.package_root / "assets" / "icons" / "maqaronydesk.png"
        )
        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))

        self.repository = ModuleRepository(self)
        self.states = ModuleStateStore(self.repository, self)
        self.watcher = FilesystemWatcher(self.library_root, self.repository, parent=self)
        self.desktop_launcher = DesktopLauncher(self.runtime_paths, self)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.navigation = NavigationWidget(self.library_root, self.repository, self.states, self.splitter)

        # Tabs are a thin presentation layer over the existing EditorManager/stack.
        # Open Markdown documents receive persistent tabs. Dashboard/folder navigation
        # surfaces use one temporary tab while consulted, then disappear as soon
        # as a document becomes active.
        self.content_host = QWidget(self.splitter)
        self.content_host.setMinimumWidth(0)
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.document_tabs = QTabBar(self.content_host)
        self.document_tabs.setDocumentMode(True)
        self.document_tabs.setMinimumWidth(0)
        self.document_tabs.setTabsClosable(True)
        self.document_tabs.setMovable(False)
        self.document_tabs.setExpanding(False)
        self.document_tabs.setUsesScrollButtons(True)
        self.document_tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.document_tabs.setVisible(False)
        self.stack = QStackedWidget(self.content_host)
        self.stack.setMinimumWidth(0)
        self.content_layout.addWidget(self.document_tabs)
        self.content_layout.addWidget(self.stack, 1)

        self.splitter.addWidget(self.navigation)
        self.splitter.addWidget(self.content_host)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        # Easier grab target without changing either pane's contents.
        self.splitter.setHandleWidth(8)
        # Keep the validated rubber-band resize path for large Grid views:
        # one layout pass on release rather than continuous reflow.
        self.splitter.setOpaqueResize(False)

        # MaqaronyPad command surface above the MaqaronyDesk workspace splitter.
        self.central_host = QWidget(self)
        self.central_layout = QVBoxLayout(self.central_host)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.tabbed_container = QWidget(self.central_host)
        self.tabbed_layout = QVBoxLayout(self.tabbed_container)
        self.tabbed_layout.setContentsMargins(0, 0, 0, 0)
        self.tabbed_layout.setSpacing(0)
        self.central_layout.addWidget(self.tabbed_container)
        self.central_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(self.central_host)

        self.editor_manager = EditorManager(
            self.library_root, self.repository, self.states, self.stack, self.config, self
        )
        self.file_actions = FileActionsController(
            self.library_root,
            self.repository,
            self.states,
            self.editor_manager,
            self.desktop_launcher,
            watcher=self.watcher,
            parent_widget=self,
            parent=self,
        )

        self.desktop_launcher.status_message.connect(self.show_status)
        self.desktop_launcher.launch_error.connect(self._show_launch_error)

        self._closing = False
        self.about_dialog: AboutDialog | None = None
        self.shortcuts_dialog: ShortcutsDialog | None = None
        self.quick_tour_dialog: QWizard | None = None
        # Temporary F10 viewing mode. The user's independent visibility choices
        # are captured and restored; Focused Mode does not rewrite them.
        self._collapsed_mode_restore: dict[str, object] | None = None
        # Browser-style context history for the dedicated mouse Back button.
        # Navigation signals are coalesced so Tabs Disabled document switches do
        # not expose the EditorManager's internal Dashboard close surface.
        self._navigation_history: list[str] = []
        self._navigation_current = "dashboard"
        self._navigation_pending: str | None = None
        self._navigation_record_scheduled = False
        self._navigation_back_in_progress = False
        self._status_label = QLabel("Ready.")
        self._repair_navigation_after_scan = False
        self._pending_open_path: Path | None = None
        self._pending_new_file_view_mode: str | None = None
        self._startup_scan_pending = True
        self._startup_open_requested = False
        status = QStatusBar(self)
        status.addWidget(self._status_label, 1)
        self.setStatusBar(status)

        self._build_menu_bar()
        self._create_tabbed_toolbar()
        self._connect_signals()
        self._sync_tabs_mode_ui()
        self._restore_window_state()
        self.watcher.start(initial_scan=True)
        self._update_action_states()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)






    def _create_tabbed_toolbar(self) -> None:
        names = (
            "new_action", "new_folder_action", "new_window_action", "dashboard_action", "workspace_tabbed_action",
            "import_file_action", "open_external_file_action", "previous_file_action", "next_file_action",
            "save_action", "save_as_action", "save_new_action", "save_dashboard_action", "save_exit_action", "exit_action",
            "properties_action", "external_editor_action", "rename_file_action", "delete_file_action",
            "duplicate_action", "open_document_folder_action", "print_action", "export_pdf_action",
            "cut_action", "copy_action", "paste_action", "paste_plain_action", "delete_text_action",
            "select_all_action", "undo_action", "redo_action", "duplicate_line_action", "delete_line_action", "comment_action",
            "find_action", "goto_action", "replace_action", "bold_action", "italic_action", "strike_action",
            "code_tabbed_action", "heading_tabbed_action", "bullet_action", "number_action", "task_action",
            "quote_action", "indent_action", "outdent_action", "rule_action", "image_action", "table_action",
            "link_tabbed_action", "link_action", "edit_link_action", "remove_link_action", "date_time_action", "date_action", "time_action", "symbol_action",
            "fullscreen_action", "status_bar_action", "sidebar_action", "word_wrap_action",
            "line_numbers_action", "editor_canvas_theme_action", "file_header_action", "view_only_action", "zoom_in_action",
            "zoom_out_action", "zoom_reset_action", "source_only_action", "split_action",
            "preview_only_action", "tab_width_action", "display_font_action", "preview_font_action",
            "collapsed_mode_action", "theme_light_action", "theme_dark_action", "theme_system_action", "icon_harmony_action", "icon_humility_action", "icon_heritage_action", "list_action", "grid_action",
            "left_sidebar_action", "right_sidebar_action", "launch_dashboard_action", "launch_last_file_action",
            "tabs_enabled_action", "tabs_disabled_action", "dirty_duplicate_tabbed_action", "dirty_external_tabbed_action",
            "docs_action", "quick_start_action", "shortcuts_action", "github_action", "issue_action",
            "about_action",
        )
        self.shell_ribbon = ShellRibbon({name: getattr(self, name) for name in names}, self.tabbed_container)
        self.tabbed_layout.addWidget(self.shell_ribbon)
        self.shell_ribbon.collapsed_changed.connect(
            lambda value: self.config.set("markopad_tabbed_collapsed", bool(value), save=True)
        )
        if bool(self.config.get("markopad_tabbed_collapsed", False)):
            self.shell_ribbon.set_collapsed(True, emit=False)


    @staticmethod
    def _widget_is_within(container: QWidget, candidate) -> bool:
        return isinstance(candidate, QWidget) and (
            candidate is container or container.isAncestorOf(candidate)
        )

    def _active_text_surface(self, page: EditorPage | None = None) -> str:
        page = self._current_page() if page is None else page
        if page is None:
            return "source"
        if page.view_mode == "preview":
            return "preview"
        if page.view_mode == "source":
            return "source"
        surface = getattr(page, "_active_text_surface", "source")
        return surface if surface in {"source", "preview"} else "source"

    def _source_interaction_active(self, page: EditorPage | None = None) -> bool:
        page = self._current_page() if page is None else page
        return bool(
            page is not None
            and page.view_mode != "preview"
            and self._active_text_surface(page) == "source"
        )

    def _editor_call(self, method: str, *args) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            getattr(page.editor, method)(*args)

    def _set_document_view(self, mode: str) -> None:
        page = self._current_page()
        if page is not None: page.set_view_mode(mode)

    def _insert_text(self, text: str) -> None:
        page = self._current_page()
        if self._source_interaction_active(page) and not page.editor.isReadOnly():
            page.editor.insert_guarded_text(text)

    def _insert_code_block(self) -> None:
        language, ok = QInputDialog.getText(self, "Code Block — MaqaronyDesk", "Language (optional):")
        if ok: self._editor_call("insert_code_fence", language)

    def _insert_link(self) -> None:
        page = self._current_page()
        if page is None: return
        selected = page.editor.textCursor().selectedText().replace("\u2029", " ")
        label, ok = QInputDialog.getText(self, "Insert Link — MaqaronyDesk", "Link text:", text=selected or "Link")
        if not ok: return
        url, ok = QInputDialog.getText(self, "Insert Link — MaqaronyDesk", "URL:")
        if ok and url.strip(): page.editor.insert_link(label, url.strip())

    def _link_at_cursor(self):
        page = self._current_page()
        if page is None: return None
        cursor = page.editor.textCursor(); block = cursor.block(); text = block.text(); pos = cursor.position() - block.position()
        for match in re.finditer(r"(?<!!)\[([^\]]*)\]\(([^\n)]*)\)", text):
            if match.start() <= pos <= match.end(): return page, block.position()+match.start(), block.position()+match.end(), match.group(1), match.group(2)
        return None

    def _edit_link(self) -> None:
        found = self._link_at_cursor()
        if not found:
            page = self._current_page()
            if page is not None:
                page.show_editor_status("Place the cursor inside a Markdown link first.")
            return
        page, start, end, label, url = found
        new_label, ok = QInputDialog.getText(self, "Edit Link — MaqaronyDesk", "Link text:", text=label)
        if not ok: return
        new_url, ok = QInputDialog.getText(self, "Edit Link — MaqaronyDesk", "URL:", text=url)
        if not ok: return
        cursor = QTextCursor(page.editor.document()); cursor.setPosition(start); cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(f"[{new_label.replace(']', r'\]')}]({new_url.replace(' ', '%20').replace(')', r'\)')})")

    def _remove_link(self) -> None:
        found = self._link_at_cursor()
        if not found:
            page = self._current_page()
            if page is not None:
                page.show_editor_status("Place the cursor inside a Markdown link first.")
            return
        page, start, end, label, _url = found
        cursor = QTextCursor(page.editor.document()); cursor.setPosition(start); cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor); cursor.insertText(label)

    def _insert_image(self) -> None:
        page = self._current_page()
        if page is None: return
        kind, ok = QInputDialog.getItem(self, "Image Reference — MaqaronyDesk", "Image source:", ["Local file (relative path)", "Web URL"], 0, False)
        if not ok: return
        if kind.startswith("Web"):
            url, ok = QInputDialog.getText(self, "Image URL — MaqaronyDesk", "URL:")
            if not ok or not url.strip(): return
            reference = url.strip().replace(" ", "%20").replace(")", r"\)"); alt_default = "Image"
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Choose Image — MaqaronyDesk", str(page.module.path.parent), "Images (*.png *.jpg *.jpeg *.gif *.webp *.svg);;All Files (*)")
            if not path: return
            target = Path(path).resolve()
            try: reference = os.path.relpath(target, page.module.path.parent).replace(os.sep, "/")
            except ValueError: QMessageBox.warning(self, "Portable Image Reference", "This image cannot be expressed as a relative path from the Markdown document."); return
            reference = reference.replace(" ", "%20").replace(")", r"\)"); alt_default = target.stem
        alt, ok = QInputDialog.getText(self, "Image Description — MaqaronyDesk", "Alternative text:", text=alt_default)
        if ok: self._insert_text(f"![{alt.replace(']', r'\]')}]({reference})")

    def _insert_table(self) -> None:
        page = self._current_page()
        if page is None: return
        dialog = QDialog(self); dialog.setWindowTitle("Table — MaqaronyDesk"); form = QFormLayout(dialog)
        rows = QSpinBox(dialog); cols = QSpinBox(dialog); rows.setRange(1,100); cols.setRange(1,20); rows.setValue(3); cols.setValue(3)
        form.addRow("Rows:", rows); form.addRow("Columns:", cols)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted: page.editor.insert_table(rows.value(), cols.value())

    def _insert_symbol(self) -> None:
        page = self._current_page()
        if page is not None:
            page.show_symbols_dialog()

    def _paste(self) -> None:
        page = self._current_page()
        if not self._source_interaction_active(page) or page.editor.isReadOnly(): return
        mime = QApplication.clipboard().mimeData()
        if mime.hasHtml():
            html = mime.html()
            if len(html) > page.editor.MAX_PASTE_CHARACTERS:
                page.show_editor_status("Clipboard HTML is too large to convert safely.")
                return
            doc = QTextDocument(); doc.setHtml(html)
            try: text = doc.toMarkdown()
            except AttributeError: text = doc.toPlainText()
            text = re.sub(r"!\[([^\]]*)\]\(data:[^\n)]*\)", lambda m: m.group(1) or "[embedded image omitted]", text, flags=re.IGNORECASE)
        else: text = mime.text() if mime.hasText() else ""
        if text:
            page.editor.insert_guarded_text(text)
        else:
            page.show_editor_status(
                "Clipboard does not contain text that can be pasted.",
                4000,
            )

    def _delete_line(self) -> None:
        page = self._current_page()
        if not self._source_interaction_active(page) or page.editor.isReadOnly(): return
        cursor = page.editor.textCursor(); cursor.beginEditBlock(); cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock); cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        if not cursor.atEnd(): cursor.deleteChar()
        elif cursor.position() > 0: cursor.deletePreviousChar()
        cursor.endEditBlock()

    def _set_editor_zoom(self, percent: int) -> None:
        if self._current_page() is None:
            return
        clamped = max(50, min(300, int(percent)))
        self.config.set("markopad_zoom", clamped, save=True)
        self.editor_manager.apply_editor_preferences()

    def _zoom_current(self, steps: int) -> None:
        current = self.config.get_int("markopad_zoom", 100, minimum=50, maximum=300)
        self._set_editor_zoom(current + (10 * int(steps)))

    def _zoom_reset(self) -> None:
        self._set_editor_zoom(100)

    def adjust_zoom_from_wheel(self, delta: int) -> None:
        """Honor MaqaronyPad's Ctrl+mouse-wheel zoom contract through the Plus shell."""
        if delta > 0:
            self._zoom_current(1)
        elif delta < 0:
            self._zoom_current(-1)


    def _save_and_exit(self) -> None:
        page = self._current_page()
        if page is None or page.save_to_disk(): self.close()

    def _save_and_new(self) -> None:
        page = self._current_page()
        if page is None or page.save_to_disk():
            self._new_markdown_file()

    def _save_and_dashboard(self) -> None:
        page = self._current_page()
        if page is None or page.save_to_disk():
            self.editor_manager.show_dashboard()

    def _rename_current(self) -> None:
        module = self._current_module()
        if module is not None:
            self.file_actions.rename_module(module)
            return
        folder = self._selected_folder()
        if folder is not None and folder != self.library_root:
            self.file_actions.rename_folder(folder)

    def _choose_tab_width(self) -> None:
        current = self.config.get_int(
            "editor_tab_width_spaces", 4, minimum=1, maximum=16
        )
        width, accepted = QInputDialog.getInt(
            self,
            "Tab Width — MaqaronyDesk",
            "Spaces per tab:",
            current,
            1,
            16,
            1,
        )
        if accepted:
            self.config.set("editor_tab_width_spaces", width, save=True)
            self.editor_manager.apply_editor_preferences()

    def _toggle_dashboard_view(self) -> None:
        self.editor_manager.dashboard.toggle_view_mode()

    def _set_dirty_duplicate_action(self, choice: str) -> None:
        if choice not in {"ask", "current", "saved"}:
            return
        self.config.set("dirty_duplicate_action", choice, save=True)
        self._on_file_policy_changed("dirty_duplicate_action", choice)

    def _set_dirty_external_action(self, choice: str) -> None:
        if choice not in {"ask", "save", "saved"}:
            return
        self.config.set("dirty_external_action", choice, save=True)
        self._on_file_policy_changed("dirty_external_action", choice)

    def _on_file_policy_changed(self, key: str, value: str) -> None:
        actions = (
            self.dirty_duplicate_actions
            if key == "dirty_duplicate_action"
            else self.dirty_external_actions
            if key == "dirty_external_action"
            else {}
        )
        for selected, action in actions.items():
            action.blockSignals(True)
            action.setChecked(selected == value)
            action.blockSignals(False)

    def _set_app_launch_screen(self, screen: str) -> None:
        if screen not in {"dashboard", "last_file"}:
            return
        self.app_launch_screen = screen
        self.launch_dashboard_action.setChecked(screen == "dashboard")
        self.launch_last_file_action.setChecked(screen == "last_file")
        self.config.set("app_launch_screen", screen, save=True)

    def _handle_editor_file_drop(
        self,
        supplied_paths: list[str | Path],
        _context_folder: str | Path | None = None,
    ) -> None:
        """Open supported editor drops in their own MaqaronyDesk windows."""
        seen: set[Path] = set()
        for supplied in supplied_paths:
            path = Path(supplied).expanduser().resolve(strict=False)
            if (
                path in seen
                or not path.is_file()
                or path.suffix.casefold() not in MARKDOWN_EXTENSIONS
            ):
                continue
            seen.add(path)
            self._launch_new_window(path)

    def _handle_app_drop(
        self,
        supplied_paths: list[str | Path],
        destination_folder: str | Path | None = None,
    ) -> None:
        """Import external Markdown drops without opening them."""
        external: list[Path] = []
        seen: set[Path] = set()
        for supplied in supplied_paths:
            path = Path(supplied).expanduser().resolve(strict=False)
            if (
                path in seen
                or not path.is_file()
                or path.suffix.casefold() not in MARKDOWN_EXTENSIONS
            ):
                continue
            seen.add(path)
            try:
                path.relative_to(self.library_root)
            except ValueError:
                external.append(path)

        if not external:
            return

        self.file_actions.import_files(
            external,
            destination_folder or self._creation_folder(),
        )

    def _delete_current_file(self) -> None:
        module = self._current_module()
        if module is not None: self.file_actions.remove_module(module)

    def _open_current_external(self) -> None:
        module = self._current_module()
        if module is not None: self.file_actions.open_external_editor(module)




    def _current_page(self) -> EditorPage | None:
        page = self.stack.currentWidget()
        return page if isinstance(page, EditorPage) else None

    def _current_module(self) -> Module | None:
        return self.editor_manager.current_module

    def _creation_folder(self) -> Path:
        """Return the folder implied by the current document or dashboard."""
        folder = self._selected_folder()
        if folder is not None:
            return folder
        module = self._current_module()
        if module is not None and not module.external:
            return module.path.parent
        return self.library_root

    def _new_markdown_file(self) -> None:
        self.file_actions.create_file(self._creation_folder())

    def _window_launch_command(self, open_path: Path | None = None) -> list[str]:
        if self.runtime_paths.running_as_appimage:
            executable = os.environ.get("APPIMAGE", "").strip()
            command = [executable] if executable else []
        elif self.runtime_paths.running_frozen:
            command = [sys.executable]
        else:
            command = [
                sys.executable,
                str(self.runtime_paths.launcher_root / "main.py"),
            ]
        if command and open_path is not None:
            command.append(str(Path(open_path).resolve(strict=False)))
        return command

    def _launch_new_window(self, open_path: Path | None = None) -> bool:
        command = self._window_launch_command(open_path)
        if not command:
            QMessageBox.warning(
                self,
                "New Window Failed",
                "MaqaronyDesk could not locate its launcher.",
            )
            return False
        try:
            subprocess.Popen(
                command,
                cwd=str(self.runtime_paths.launcher_root),
                start_new_session=True,
            )
        except OSError as error:
            QMessageBox.warning(
                self,
                "New Window Failed",
                f"MaqaronyDesk could not open a new window:\n\n{error}",
            )
            return False
        return True

    def _new_window(self) -> None:
        self._launch_new_window()

    def _import_file_into_workspace(self) -> None:
        patterns = "*.md *.markdown *.mdown *.mkd"
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Import File into Workspace — MaqaronyDesk",
            "",
            f"Markdown Files ({patterns})",
        )
        if not selected:
            return
        # Reuse the exact external-drop import path: validate as external
        # Markdown, copy into the Workspace root, rescan, and stop without opening.
        self._handle_app_drop([Path(selected)], self.library_root)

    def _open_external_file(self) -> None:
        patterns = "*.md *.markdown *.mdown *.mkd"
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Open External File — MaqaronyDesk",
            "",
            f"Markdown Files ({patterns})",
        )
        if not selected:
            return
        path = Path(selected).expanduser().resolve(strict=False)
        if not path.is_file() or path.suffix.casefold() not in MARKDOWN_EXTENSIONS:
            QMessageBox.warning(
                self,
                "Open External File Failed",
                "Choose a supported Markdown file (.md, .markdown, .mdown, or .mkd).",
            )
            return
        try:
            path.relative_to(self.library_root)
        except ValueError:
            self._launch_new_window(path)
            return
        QMessageBox.information(
            self,
            "Managed Workspace File",
            "That file belongs to the active Workspace. Open it from the Workspace instead.",
        )

    def _new_folder(self) -> None:
        created = self.file_actions.create_folder(self._creation_folder())
        if created is not None:
            # Empty folders contain no modules, so a repository rescan alone
            # cannot add them to the document-derived tree. Rebuild the tree
            # after the directory is created so the folder appears at once.
            QTimer.singleShot(100, self.navigation.rebuild_from_repository)

    def _show_projects(self) -> None:
        dialog = ProjectsDialog(self.project_registry, self)
        result = dialog.exec()
        if (
            result == QDialog.DialogCode.Accepted
            and dialog.selected_project_id
        ):
            self._switch_project(dialog.selected_project_id)
        self._update_window_title()
        self._rebuild_workspace_menu()

    def _rebuild_workspace_menu(self) -> None:
        """Build the radio inventory only from the lightweight registry."""
        for action in tuple(self.workspace_action_group.actions()):
            self.workspace_action_group.removeAction(action)
            self.workspace_menu.removeAction(action)
            action.deleteLater()
        self.workspace_menu.clear()
        self.workspace_menu.addAction(self.manage_workspaces_action)
        self.workspace_menu.addSeparator()

        active_id = self.project_registry.active_project_id
        for workspace in self.project_registry.projects:
            action = QAction(workspace.name, self.workspace_menu)
            action.setCheckable(True)
            action.setChecked(workspace.project_id == active_id)
            action.setData(workspace.project_id)
            action.setToolTip(str(workspace.folder))
            action.setStatusTip(str(workspace.folder))
            action.triggered.connect(
                lambda _checked=False, workspace_id=workspace.project_id:
                self._switch_project(workspace_id)
            )
            self.workspace_action_group.addAction(action)
            self.workspace_menu.addAction(action)


    def _switch_project(self, project_id: str) -> bool:
        project = self.project_registry.get(project_id)
        if project is None:
            return False
        if project.project_id == self.project_registry.active_project_id:
            self._update_window_title()
            self.editor_manager.show_dashboard()
            return True
        if not project.folder.is_dir():
            QMessageBox.warning(
                self,
                "Workspace Folder Unavailable",
                "Relink this Workspace to an available folder before opening it.",
            )
            return False
        try:
            project_root = self.runtime_paths.ensure_writable_workspace(project.folder)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Workspace Cannot Be Opened",
                f"MaqaronyDesk could not use this Workspace folder:\n\n{error}",
            )
            return False
        if not self.editor_manager.can_close_application():
            return False

        self._save_active_project_state(save=True)
        stopped = self.watcher.stop(
            timeout_ms=2500,
            pump_events=QApplication.processEvents,
        )
        if not stopped:
            self._install_watcher(self.library_root, start=True, retire_current=False)
            QMessageBox.warning(
                self,
                "Workspace Switch Cancelled",
                "The current Workspace scanner did not stop safely. "
                "The existing Workspace remains active.",
            )
            return False

        self._pending_open_path = None
        self._pending_new_file_view_mode = None
        self._repair_navigation_after_scan = False
        self.library_root = project_root
        self.editor_manager.switch_workspace_root(project_root)
        self.navigation.switch_workspace_root(project_root)
        self.repository.clear()
        self.project_registry.set_active(project.project_id)
        self._apply_active_project_state()
        self._install_watcher(project_root, start=True, retire_current=True)
        self.editor_manager.show_dashboard()
        self._update_action_states()
        self.show_status(f"Opening Workspace: {project.name}")
        return True


    def _selected_folder(self) -> Path | None:
        return self.editor_manager.current_folder

    def _open_current_document_folder(self) -> None:
        module = self._current_module()
        if module is not None:
            self.file_actions.open_module_folder(module)

    def _open_current_folder_external(self) -> None:
        folder = self._selected_folder()
        if folder is not None:
            self.file_actions.open_folder_external(folder)

    def _rename_current_folder(self) -> None:
        folder = self._selected_folder()
        if folder is not None:
            self.file_actions.rename_folder(folder)

    def _remove_current_folder(self) -> None:
        folder = self._selected_folder()
        if folder is not None:
            self.file_actions.remove_folder(folder)

    def _save_current(self) -> None:
        page = self._current_page()
        if page:
            page.save_to_disk()

    def _save_external_change_version_as(self, page: EditorPage) -> bool:
        """Preserve the live Marko version while leaving the changed source untouched."""
        source_path = page.module.path.resolve(strict=False)
        suffix = source_path.suffix or ".md"
        suggested = source_path.with_name(
            f"{source_path.stem} - Desk Version{suffix}"
        )
        counter = 2
        while suggested.exists():
            suggested = source_path.with_name(
                f"{source_path.stem} - Desk Version {counter}{suffix}"
            )
            counter += 1

        extensions = " ".join(f"*{ext}" for ext in sorted(MARKDOWN_EXTENSIONS))
        while True:
            selected, _ = QFileDialog.getSaveFileName(
                self,
                "Save Version As — MaqaronyDesk",
                str(suggested),
                f"Markdown ({extensions});;All Files (*)",
            )
            if not selected:
                return False

            target = Path(selected).expanduser().resolve(strict=False)
            if not target.suffix:
                target = target.with_suffix(".md")
            if target.suffix.casefold() not in MARKDOWN_EXTENSIONS:
                QMessageBox.warning(
                    self,
                    "Unsupported Extension — MaqaronyDesk",
                    "MaqaronyDesk saves Markdown documents only.",
                )
                suggested = target
                continue
            if target == source_path:
                QMessageBox.warning(
                    self,
                    "Save Version As — MaqaronyDesk",
                    "Choose a different filename. The original file changed "
                    "externally and will be left untouched.",
                )
                suggested = target
                continue
            existing = self.repository.get(target)
            if existing is not None:
                state = self.states.get(target)
                if state is not None and isinstance(state.editor_page, EditorPage):
                    QMessageBox.warning(
                        self,
                        "Save Version As — MaqaronyDesk",
                        "That Markdown file is already open in another editor page. "
                        "Close it before replacing it with Save Version As.",
                    )
                    suggested = target
                    continue

            page._save_version_status_override = (
                f"Saved MaqaronyDesk version as {target.name}; external disk copy preserved."
            )
            try:
                return bool(page.save_as_file(target))
            finally:
                page._save_version_status_override = None

    def _save_current_as(self) -> None:
        page = self._current_page()
        module = self._current_module()
        if page is None or module is None:
            return

        extensions = " ".join(f"*{ext}" for ext in sorted(MARKDOWN_EXTENSIONS))
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Save As — MaqaronyDesk",
            str(module.path),
            f"Markdown ({extensions});;All Files (*)",
        )
        if not selected:
            return

        target = Path(selected).expanduser().resolve(strict=False)
        if not target.suffix:
            target = target.with_suffix(".md")
        if target.suffix.casefold() not in MARKDOWN_EXTENSIONS:
            QMessageBox.warning(
                self,
                "Unsupported Extension — MaqaronyDesk",
                "MaqaronyDesk saves Markdown documents only.",
            )
            return
        if target == module.path.resolve(strict=False):
            page.save_to_disk()
            return

        existing = self.repository.get(target)
        if existing is not None:
            state = self.states.get(target)
            if state is not None and isinstance(state.editor_page, EditorPage):
                QMessageBox.warning(
                    self,
                    "Save As — MaqaronyDesk",
                    "That Markdown file is already open in another editor page. "
                    "Close it before replacing it with Save As.",
                )
                return

        if not page.save_as_file(target):
            return


    def _undo(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.undo()

    def _redo(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.redo()

    def _cut(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.cut()

    def _copy(self) -> None:
        page = self._current_page()
        if page is None:
            return
        if self._active_text_surface(page) == "preview":
            page.preview.copy()
        else:
            page.editor.copy()

    def _delete_text(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.delete_selection_or_character()

    def _toggle_comment(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.toggle_comment()

    def _duplicate_line(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.duplicate_current_line_or_selection()

    def _paste_plain_text(self) -> None:
        page = self._current_page()
        if self._source_interaction_active(page):
            page.editor.paste_safely()

    def _select_all(self) -> None:
        page = self._current_page()
        if page is None:
            return
        if self._active_text_surface(page) == "preview":
            page.preview.selectAll()
        else:
            page.editor.select_all_text()

    def _duplicate_current(self) -> None:
        module = self._current_module()
        if module is not None:
            self.file_actions.duplicate_module(module)

    def _focus_find(self) -> None:
        """Ctrl+F toggles document Find when focused there, or targets navigation search."""
        page = self._current_page()
        if page is not None:
            page.toggle_find_panel(False)
            return

        search = getattr(self.stack.currentWidget(), "search_input", None)
        if search is not None:
            search.setFocus(Qt.FocusReason.ShortcutFocusReason)
            search.selectAll()

    def _focus_replace(self) -> None:
        page = self._current_page()
        if page:
            page.toggle_find_panel(True)

    def _go_to_line(self) -> None:
        page = self._current_page()
        if page:
            page.show_go_to_line()

    def _show_properties(self) -> None:
        page = self._current_page()
        if page:
            page.show_properties_dialog()

    def _toggle_lock_editor_current(self, checked: bool) -> None:
        # Preserve Marko's protective unlock warning, then make the resulting
        # lock state application-wide so it follows the user across files and
        # survives the next session.
        page = self._current_page()
        if page is None:
            self.view_only_action.blockSignals(True)
            self.view_only_action.setChecked(
                bool(self.config.get("lock_editor", False))
            )
            self.view_only_action.blockSignals(False)
            return
        desired = bool(checked)
        source = page.view_only_action
        if bool(page.view_only) != desired:
            source.trigger()
        resulting = bool(page.view_only)
        self.editor_manager.set_lock_editor(resulting)
        self._sync_editor_view_actions()
        self._update_action_states()
        self._update_window_title()

    def _toggle_word_wrap(self, checked: bool) -> None:
        page = self._current_page()
        if page:
            page.word_wrap_action.setChecked(bool(checked))
            page.toggle_word_wrap(bool(checked))

    def _toggle_line_numbers(self, checked: bool) -> None:
        page = self._current_page()
        if page:
            page.line_numbers_action.setChecked(bool(checked))
            page.toggle_line_numbers(bool(checked))





    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            page = self._current_page()
            if page is not None:
                surface = None
                if self._widget_is_within(page.editor, watched):
                    surface = "source"
                elif self._widget_is_within(page.preview, watched):
                    surface = "preview"
                if surface is not None and surface != getattr(page, "_active_text_surface", None):
                    page._active_text_surface = surface
                    self._update_action_states()
        if event.type() == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
            page = self._current_page()
            if (
                page is not None
                and page.view_mode == "split"
                and watched is page.content_splitter.handle(1)
            ):
                page.reset_content_splitter()
                event.accept()
                return True
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and self.isActiveWindow()
            and event.button() == Qt.MouseButton.BackButton
        ):
            self._navigate_back()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def _open_sidebar_module(self, path):
        """Open a sidebar document transactionally and roll back rejected selection."""
        page = self.editor_manager.open_module(path)
        if page is None:
            current = self.editor_manager.current_module
            if current is not None and not current.external:
                self.navigation.select_module(current.path)
        return page

    def _connect_signals(self) -> None:
        self.document_tabs.currentChanged.connect(self._activate_document_tab)
        self.document_tabs.tabCloseRequested.connect(self._close_document_tab)

        self.navigation.dashboard_requested.connect(self.editor_manager.show_dashboard)
        self.navigation.refresh_requested.connect(self._refresh_workspace)
        self.navigation.folder_requested.connect(self.editor_manager.open_folder)
        self.navigation.module_requested.connect(self._open_sidebar_module)
        self.navigation.module_move_requested.connect(self.file_actions.move_module)
        self.navigation.external_files_import_requested.connect(
            self.file_actions.import_files
        )
        self.editor_manager.dashboard_shown.connect(self.navigation.select_dashboard)
        self.editor_manager.dashboard_shown.connect(self._record_dashboard_navigation)
        self.editor_manager.dashboard_shown.connect(self._show_dashboard_navigation_tab)
        self.editor_manager.dashboard_shown.connect(self._update_action_states)
        self.editor_manager.dashboard_shown.connect(self._sync_editor_view_actions)
        self.editor_manager.current_folder_changed.connect(self.navigation.select_folder)
        self.editor_manager.current_folder_changed.connect(self._record_folder_navigation)
        self.editor_manager.current_folder_changed.connect(self._show_folder_navigation_tab)
        self.editor_manager.current_folder_changed.connect(self._update_action_states)
        self.editor_manager.current_module_changed.connect(self._select_document_tab)
        self.editor_manager.current_module_changed.connect(self._record_module_navigation)
        self.editor_manager.current_module_changed.connect(
            lambda module: (
                self.navigation.select_module(module.path)
                if not module.external else False
            )
        )
        self.editor_manager.current_module_changed.connect(self._remember_last_opened_module)
        self.editor_manager.current_module_changed.connect(self._update_action_states)
        self.editor_manager.current_module_changed.connect(lambda _module: self._sync_editor_view_actions())
        self.editor_manager.external_editor_requested.connect(
            self.file_actions.open_external_editor
        )
        self.editor_manager.containing_folder_requested.connect(
            self.file_actions.open_module_folder
        )
        self.editor_manager.rename_requested.connect(self.file_actions.rename_module)
        self.editor_manager.remove_requested.connect(self.file_actions.remove_module)
        self.editor_manager.duplicate_requested.connect(
            self.file_actions.duplicate_module
        )
        self.editor_manager.editor_history_changed.connect(
            self._on_editor_history_changed
        )
        self.editor_manager.editor_preferences_changed.connect(
            self._sync_editor_view_actions
        )
        self.editor_manager.editor_preferences_changed.connect(
            self._update_action_states
        )
        self.editor_manager.folder_open_external_requested.connect(self.file_actions.open_folder_external)
        self.editor_manager.folder_rename_requested.connect(self.file_actions.rename_folder)
        self.editor_manager.folder_remove_requested.connect(self.file_actions.remove_folder)
        self.editor_manager.create_file_requested.connect(self.file_actions.create_file)
        self.editor_manager.create_folder_requested.connect(self._create_folder_from_dashboard)
        self.editor_manager.external_files_import_requested.connect(
            self.file_actions.import_files
        )
        self.editor_manager.editor_files_dropped.connect(self._handle_editor_file_drop)
        self.editor_manager.refresh_requested.connect(self._refresh_workspace)
        self.editor_manager.sort_mode_changed.connect(self._remember_sort_mode)
        self.editor_manager.view_mode_changed.connect(self._remember_view_mode)
        self.editor_manager.view_mode_changed.connect(self._sync_view_actions)
        self.editor_manager.module_path_rebound.connect(self._rebind_document_tab)
        self.editor_manager.module_path_rebound.connect(lambda _old, _new: self.watcher.request_rescan())
        self.editor_manager.module_closed.connect(self._remove_document_tab)
        self.editor_manager.modules_reset.connect(self._reset_document_tabs)
        self.file_actions.folder_renamed.connect(self._on_folder_renamed)
        self.file_actions.folder_removed.connect(lambda _path: self.editor_manager.show_dashboard())
        self.file_actions.module_created.connect(self._queue_created_open)
        self.file_actions.file_policy_changed.connect(self._on_file_policy_changed)
        self.repository.module_added.connect(self._open_pending_if_ready)
        for source in (self.editor_manager, self.file_actions):
            source.status_message.connect(self.show_status)
        self._connect_watcher_signals(self.watcher)
        self.repository.dirty_count_changed.connect(self._update_dirty_status)
        self.repository.module_changed.connect(self._update_document_tab)
        self.repository.module_changed.connect(lambda _module: self._update_action_states())
        self.repository.module_path_changed.connect(self._remember_renamed_module_path)
        self.repository.module_path_changed.connect(self._on_repository_module_path_changed)
        self.repository.module_path_changed.connect(lambda _module, _old: self._update_action_states())

    def _connect_watcher_signals(self, watcher: FilesystemWatcher) -> None:
        watcher.scan_started.connect(self._on_scan_started)
        watcher.folders_discovered.connect(self.navigation.set_disk_folders)
        watcher.scan_details.connect(self._on_scan_details)
        watcher.scan_finished.connect(self._on_scan_finished)
        watcher.scan_failed.connect(self._on_scan_failed)

    def _install_watcher(
        self,
        library_root: Path,
        *,
        start: bool,
        retire_current: bool,
    ) -> None:
        previous = self.watcher
        watcher = FilesystemWatcher(library_root, self.repository, parent=self)
        self.watcher = watcher
        self.file_actions.switch_workspace_root(library_root, watcher)
        self._connect_watcher_signals(watcher)
        if start:
            watcher.start(initial_scan=True)
        if retire_current and previous is not watcher:
            previous.deleteLater()

    def _create_folder_from_dashboard(self, parent: Path) -> None:
        created = self.file_actions.create_folder(parent)
        if created is not None:
            QTimer.singleShot(100, self.navigation.rebuild_from_repository)

    def _queue_created_open(self, path: Path) -> None:
        self._startup_open_requested = True
        preferred = str(self.config.get("markopad_last_editable_view_mode", ""))
        if preferred not in {"source", "split"}:
            current = str(self.config.get("markopad_view_mode", "split"))
            preferred = current if current in {"source", "split"} else "split"
        self._pending_new_file_view_mode = preferred
        self._pending_open_path = Path(path).resolve(strict=False)
        module = self.repository.get(self._pending_open_path)
        if module is not None:
            self._open_pending_if_ready(module)

    def queue_open_path(self, path: str | Path) -> None:
        """Open a path without importing external OS-open documents."""
        self._pending_new_file_view_mode = None
        target = Path(path).expanduser().resolve(strict=False)
        if not target.is_file() or target.suffix.casefold() not in MARKDOWN_EXTENSIONS:
            return
        self._startup_open_requested = True
        try:
            target.relative_to(self.library_root)
        except ValueError:
            self._open_external_path(target)
            return
        self._pending_open_path = target
        module = self.repository.get(target)
        if module is not None:
            self._open_pending_if_ready(module)
        elif not self._startup_scan_pending:
            self.watcher.request_rescan()

    def _open_external_path(self, path: Path) -> None:
        try:
            info = path.stat()
        except OSError:
            return
        module = self.repository.get(path)
        if module is None:
            module = self.repository.add(
                Module(
                    path=path,
                    filename=path.name,
                    display_name=path.stem.replace("-", " ").replace("_", " ").title(),
                    folder=str(path.parent),
                    created=info.st_ctime,
                    modified=info.st_mtime,
                    size=info.st_size,
                    external=True,
                )
            )
        page = self.editor_manager.open_module(module)
        if page is None:
            self.repository.remove(path)
            return
        self._apply_external_verification_mode(page)

    def _apply_external_verification_mode(self, page: EditorPage) -> None:
        """Start an externally launched document in transient Preview + Locked + Focused Mode."""
        page.set_view_mode("preview", persist=False)
        page.set_view_only(True)
        page.scroll_to_top()
        self._sync_editor_view_actions()
        self.collapsed_mode_action.blockSignals(True)
        self.collapsed_mode_action.setChecked(True)
        self.collapsed_mode_action.blockSignals(False)
        self._toggle_collapsed_mode(True)
        self._update_action_states()
        self._update_window_title()

    def _open_pending_if_ready(self, module: Module) -> None:
        if (
            self._pending_open_path is None
            or module.path.resolve(strict=False) != self._pending_open_path
        ):
            return
        self._pending_open_path = None
        preferred = self._pending_new_file_view_mode
        self._pending_new_file_view_mode = None
        page = self.editor_manager.open_module(module)
        if page is not None and preferred in {"source", "split"}:
            page.set_view_mode(preferred, persist=False)

    def _sync_view_actions(self, mode: str) -> None:
        self.list_action.setChecked(mode == "list")
        self.grid_action.setChecked(mode == "grid")

    def _remember_last_opened_module(self, module: Module) -> None:
        if module.external:
            return
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"last_opened_file": str(module.path)},
        )

    def _remember_renamed_module_path(
        self,
        module: Module,
        old_path: Path,
    ) -> None:
        if module.external:
            return
        last_path = self.project_registry.active_project.state.get(
            "last_opened_file"
        )
        if not last_path:
            return
        if Path(str(last_path)).resolve(strict=False) != Path(old_path).resolve(
            strict=False
        ):
            return
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"last_opened_file": str(module.path)},
        )

    def _on_editor_history_changed(
        self,
        undo_available: bool,
        redo_available: bool,
    ) -> None:
        page = self._current_page()
        if page is None:
            return
        source_active = self._source_interaction_active(page)
        self.undo_action.setEnabled(undo_available and source_active)
        self.redo_action.setEnabled(redo_available and source_active)


    def _on_folder_renamed(self, old_path: Path, new_path: Path) -> None:
        QTimer.singleShot(600, lambda: self.editor_manager.open_folder(new_path))

    def _restore_window_state(self) -> None:
        width = self.config.get_int("window_width", 1350, minimum=900)
        height = self.config.get_int("window_height", 850, minimum=600)
        self.resize(width, height)
        sizes = self.config.get_int_list(
            "splitter_sizes",
            [260, 1090],
            length=2,
        )
        self._restored_sidebar_width = (
            int(sizes[0]) if sizes and int(sizes[0]) > 0 else 260
        )
        self._set_sidebar_position(
            str(self.config.get("sidebar_position", "left")), persist=False
        )
        # Restore after Qt has a real central-widget geometry. This avoids
        # stale total widths producing a jumpy or apparently stuck handle.
        QTimer.singleShot(0, self._restore_splitter_geometry)

        self._apply_active_project_state()
        if bool(self.config.get("window_maximized", False)):
            self.showMaximized()

    def _apply_active_project_state(self) -> None:
        self._update_window_title()
        state = self.project_registry.active_project.state
        folders = state.get("collapsed_folders", [])
        if isinstance(folders, list):
            self.navigation.restore_collapsed_folders(folders)
        sort_mode = str(state.get("dashboard_sort", "modified"))
        search_text = str(state.get("dashboard_search", ""))
        view_mode = str(state.get("dashboard_view", "list"))
        self.editor_manager.set_sort_mode(sort_mode)
        self.editor_manager.set_search_text(search_text)
        self.editor_manager.set_view_mode(view_mode)
        self._sync_view_actions(view_mode)

    def _update_window_title(self) -> None:
        workspace = self.project_registry.active_project.name.strip()
        module = self.editor_manager.current_module
        if module is not None:
            scope = "External" if module.external else workspace
            page = self._current_page()
            lock_suffix = " — Locked Mode" if page is not None and page.view_only else ""
            dirty_prefix = "*" if module.dirty else ""
            self.setWindowTitle(
                f"{dirty_prefix}{module.filename} — {scope} — {APP_NAME}{lock_suffix}"
            )
        else:
            self.setWindowTitle(f"{workspace} — {APP_NAME}")

    def _save_active_project_state(self, *, save: bool) -> None:
        values: dict[str, object] = {
            "collapsed_folders": sorted(self.navigation.collapsed_folders()),
            "dashboard_sort": self.editor_manager.dashboard._sort_mode,
            "dashboard_search": self.editor_manager.dashboard.search_input.text(),
            "dashboard_view": self.editor_manager.dashboard.view_mode(),
            "last_opened_folder": (
                str(self.editor_manager.current_folder)
                if self.editor_manager.current_folder is not None
                else None
            ),
        }
        # Last File means the most recently opened document, even if the user
        # returns to Dashboard before quitting. Do not erase that history merely
        # because no editor page is current at shutdown or Workspace switch.
        module = self.editor_manager.current_module
        if module is not None and not module.external:
            values["last_opened_file"] = str(module.path)
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            values,
            save=save,
        )

    def _restore_splitter_geometry(self) -> None:
        """Restore sidebar width against the live splitter geometry."""
        self._set_splitter_sidebar_width(
            int(getattr(self, "_restored_sidebar_width", 260))
        )

    def _refresh_workspace(self) -> None:
        """Run one background scan, then repair navigation from its result."""
        self._repair_navigation_after_scan = True
        self.show_status("Refreshing workspace in background…")
        self.watcher.request_rescan()

    def _on_scan_started(self) -> None:
        message = (
            "Refreshing your workspace…"
            if self._repair_navigation_after_scan
            else "Preparing your workspace…"
        )
        self.editor_manager.dashboard.set_loading(True, message)
        self.navigation.set_loading(True, "Building folder tree…")
        self.show_status("Scanning workspace in background…")

    def _on_scan_details(self, entries: int, seconds: float) -> None:
        detail = f"Scanned {entries:,} filesystem entries in {seconds:.1f}s."
        self.editor_manager.dashboard.set_loading_detail(detail)
        self.navigation.set_loading_detail(
            f"{sum(1 for module in self.repository if not module.external):,} Markdown files found"
        )
        self.show_status(detail)

    def _on_scan_finished(self, count: int) -> None:
        self.editor_manager.dashboard.set_loading(False)
        self.navigation.set_loading(False)
        project_name = self.project_registry.active_project.name
        if self._repair_navigation_after_scan:
            self._repair_navigation_after_scan = False
            self.navigation.rebuild_from_repository()
            self.show_status(
                f"Refreshed {count} Markdown file(s) in {project_name}."
            )
        else:
            self.show_status(
                f"Loaded {count} Markdown file(s) in {project_name}."
            )
        if self._pending_open_path is not None:
            module = self.repository.get(self._pending_open_path)
            if module is not None:
                self._open_pending_if_ready(module)
        if not self._startup_scan_pending:
            return
        self._startup_scan_pending = False
        if self._startup_open_requested:
            return
        if self.app_launch_screen != "last_file":
            self.editor_manager.show_dashboard()
            return
        project_state = self.project_registry.active_project.state
        last_path = project_state.get("last_opened_file")
        if last_path:
            module = self.repository.get(last_path)
            if module is not None:
                self.editor_manager.open_module(module)
                return
        self.editor_manager.show_dashboard()

    def _on_scan_failed(self, message: str) -> None:
        self.editor_manager.dashboard.set_loading(False)
        self.navigation.set_loading(False)
        self.show_status(f"Workspace scan failed: {message}")
        QMessageBox.warning(self, "Workspace Scan Failed", message)

    def _remember_sort_mode(self, mode: str) -> None:
        self.config.set("dashboard_sort", mode)
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"dashboard_sort": mode},
        )

    def _remember_view_mode(self, mode: str) -> None:
        self.config.set("dashboard_view", mode)
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"dashboard_view": mode},
        )

    def _update_dirty_status(self, count: int) -> None:
        if count:
            self.show_status(f"{count} Markdown file has unsaved changes." if count == 1 else f"{count} Markdown files have unsaved changes.")

    def _show_launch_error(self, message: str) -> None:
        QMessageBox.warning(self, "Could Not Open", message)

    def show_status(self, message: str) -> None:
        from maqarony_desk.widgets.message_conventions import (
            DEFAULT_MESSAGE_DURATION_MS, is_critical_status, status_sentence,
        )
        text = status_sentence(message)
        critical = is_critical_status(text)
        # An unresolved failure stays visible until a deliberate retry/success
        # or another critical event replaces it. Routine notices cannot hide it.
        recovering = text.startswith((
            "Opening Workspace:", "Refreshing workspace", "Scanning workspace",
            "Refreshed ", "Loaded ",
        ))
        if getattr(self, "_critical_workspace_message", False) and not (critical or recovering):
            return
        self._critical_workspace_message = critical
        self._status_label.setText(text)
        timer = getattr(self, "_workspace_message_timer", None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._status_label.setText("Ready."))
            self._workspace_message_timer = timer
        timer.stop()
        if not is_critical_status(text):
            timer.start(DEFAULT_MESSAGE_DURATION_MS)

    def _write_shutdown_timing(self, timings: dict[str, float]) -> None:
        """Write shutdown diagnostics only when explicitly requested."""
        enabled = os.environ.get(SHUTDOWN_PROFILE_ENV, "").casefold()
        if enabled not in {"1", "true", "yes", "on"}:
            return

        report_path = self.runtime_paths.config_root / "shutdown-timing.jsonl"
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "documents": len(self.repository),
            "timings_ms": {
                key: round(value * 1000.0, 2)
                for key, value in timings.items()
            },
        }
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        except OSError:
            pass

        printable = " · ".join(
            f"{key}={value * 1000.0:.1f} ms"
            for key, value in timings.items()
        )
        print(f"MaqaronyDesk shutdown: {printable}", flush=True)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._closing:
            event.accept()
            return

        started = time.perf_counter()
        timings: dict[str, float] = {}

        unsaved_started = time.perf_counter()
        if not self.editor_manager.can_close_application():
            timings["unsaved_prompt"] = time.perf_counter() - unsaved_started
            event.ignore()
            return
        timings["unsaved_prompt"] = time.perf_counter() - unsaved_started

        self._closing = True

        closing_dialog = ClosingDialog(self)
        closing_dialog.start()
        QApplication.processEvents()

        def stage(detail: str) -> None:
            closing_dialog.set_stage(detail)
            QApplication.processEvents()

        stage("Saving your preferences…")
        config_started = time.perf_counter()
        self._save_active_project_state(save=True)
        self.config.update(
            {
                "window_width": self.width(),
                "window_height": self.height(),
                "window_maximized": self.isMaximized(),
                "splitter_sizes": (
                    list(
                        self._collapsed_mode_restore.get(
                            "splitter_sizes", self._logical_splitter_sizes()
                        )
                    )
                    if self._collapsed_mode_restore is not None
                    else self._logical_splitter_sizes()
                ),
                "collapsed_folders": sorted(
                    self.navigation.collapsed_folders()
                ),
                "dashboard_sort": self.editor_manager.dashboard._sort_mode,
                "dashboard_search": (
                    self.editor_manager.dashboard.search_input.text()
                ),
                "dashboard_view": (
                    self.editor_manager.dashboard.view_mode()
                ),
                # Compatibility mirror for the application-level fallback.
                # The per-Workspace value preserved above is authoritative.
                "last_opened_file": self.project_registry.active_project.state.get(
                    "last_opened_file"
                ),
                "last_opened_folder": (
                    str(self.editor_manager.current_folder)
                    if self.editor_manager.current_folder is not None
                    else None
                ),
            },
            save=True,
        )
        timings["save_config"] = time.perf_counter() - config_started

        # Hide the main hierarchy without rebuilding Dashboard cards on exit.
        # The Dashboard is not becoming interactive on a successful close.
        self.navigation.set_loading(False)
        self.centralWidget().hide()
        self.menuBar().hide()
        self.statusBar().hide()
        closing_dialog.adjustSize()
        closing_dialog.move(
            self.frameGeometry().center()
            - closing_dialog.rect().center()
        )
        QApplication.processEvents()

        stage("Stopping the workspace scanner…")
        scanner_started = time.perf_counter()
        scan_stopped = self.watcher.stop(
            timeout_ms=2000,
            pump_events=QApplication.processEvents,
        )
        timings["stop_scanner"] = time.perf_counter() - scanner_started

        if not scan_stopped:
            self._closing = False
            closing_dialog.close()
            # Shutdown was cancelled: restore the normal, usable Dashboard.
            self.editor_manager.dashboard.set_loading(False)
            self.centralWidget().show()
            self.menuBar().show()
            self.statusBar().show()
            self.show_status("Could not cancel the workspace scan yet.")
            event.ignore()
            return

        timings["total_before_exit"] = time.perf_counter() - started
        self._write_shutdown_timing(timings)

        stage("Closing MaqaronyDesk…")
        event.accept()
        QApplication.processEvents()

        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os._exit(0)
