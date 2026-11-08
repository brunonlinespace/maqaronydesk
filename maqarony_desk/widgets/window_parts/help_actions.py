# MaqaronyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing MainWindow Help and Quick Tour methods, relocated without behaviour changes."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox, QLabel, QMenu, QMessageBox, QPushButton,
    QVBoxLayout, QWizard, QWizardPage,
)
from maqarony_desk.app_constants import GITHUB_URL, ISSUES_URL
from maqarony_desk.widgets.dialogs.about_dialog import AboutDialog
from maqarony_desk.widgets.dialogs.shortcuts_dialog import ShortcutsDialog


class HelpActionsMixin:
    def _show_quick_tour(self) -> None:
        """Show the richer first-run tour in Ricopad's wizard style."""
        if self.quick_tour_dialog is not None:
            self.quick_tour_dialog.show()
            self.quick_tour_dialog.raise_()
            self.quick_tour_dialog.activateWindow()
            return

        wizard = QWizard(self)
        wizard.setWindowTitle("Quick Tour — MaqaronyDesk")
        wizard.setWindowIcon(self.windowIcon())
        wizard.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        wizard.setModal(False)
        wizard.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        wizard.setMinimumSize(700, 470)
        wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        startup_checkbox = QCheckBox("Don't show Quick Tour on startup again", wizard)
        startup_checkbox.setChecked(bool(self.config.get("quick_tour_seen", False)))
        startup_checkbox.toggled.connect(
            lambda checked: self.config.set("quick_tour_seen", bool(checked), save=True)
        )
        wizard.setButton(QWizard.WizardButton.CustomButton1, startup_checkbox)
        wizard.setOption(QWizard.WizardOption.HaveCustomButton1, True)
        wizard.setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.FinishButton,
            QWizard.WizardButton.CancelButton,
        ])

        def add_page(title: str, subtitle: str, body: str, button=None) -> None:
            page = QWizardPage(wizard)
            page.setTitle(title)
            page.setSubTitle(subtitle)
            layout = QVBoxLayout(page)
            label = QLabel(body, page)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(label)
            if button is not None:
                layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addStretch(1)
            wizard.addPage(page)

        add_page(
            "Welcome to MaqaronyDesk",
            "A workspace-scale MaqaronyPad for ordinary Markdown files.",
            "<p>The command bar has six tabs: <b>File, Home, Insert, View, Settings "
            "and Help</b>, with Home open by default.</p>"
            "<p>When document tabs are <b>enabled</b>, <b>Ctrl+Tab</b> and "
            "<b>Ctrl+Shift+Tab</b> move forward and backward through open document "
            "and navigation tabs. When document tabs are <b>disabled</b>, the same "
            "shortcuts move through command-bar pages instead.</p>"
            "<p><b>Ctrl+T</b> opens the current navigation context as a tab, enabling "
            "tabs first if necessary. <b>Ctrl+W</b> closes the active document tab "
            "when tabs are enabled and returns to its folder context; with tabs "
            "disabled, or no active document, it returns to Dashboard.</p>"
            "<p>Double-click a command-bar tab title to collapse its controls; click "
            "a tab title to reveal them again.</p>",
        )
        add_page(
            "Workspaces and Dashboard",
            "Keep separate Markdown collections without moving the application.",
            "<p><b>File → Workspace(s)</b> lists registered Workspaces and marks "
            "the active one. <b>Open / Manage Workspaces...</b> adds an existing folder, "
            "renames its display label, relinks it, or removes only its "
            "registration.</p>"
            "<p>Only the active Workspace is scanned and watched. On the "
            "Dashboard, one click selects a card and double-click opens Edit. "
            "Each card also provides <b>Edit, Split View and Preview</b>.</p>",
        )
        add_page(
            "Folders and files",
            "Create documents where you are already working.",
            "<p>New File uses the open folder dashboard, the active "
            "document's containing folder, or the Workspace root when the main "
            "Dashboard is open. The new file opens as soon as its name is "
            "saved.</p>"
            "<p>Use <b>Ctrl+Up</b> and <b>Ctrl+Down</b> for adjacent Markdown "
            "files shown in the folder tree. External files dropped on a folder "
            "are imported there; internal cards can be dragged onto sidebar "
            "folders to move them.</p>",
        )
        add_page(
            "Edit and preview",
            "Use MaqaronyPad's three document layouts and Markdown commands.",
            "<p><b>Source Only, Source + Preview and Preview Only</b> are "
            "available from View. Home and Insert provide Markdown formatting, "
            "headings, lists, links, images, tables, rules, dates, times and "
            "symbols.</p>"
            "<p>Locked Mode protects source text from accidental edits and stays "
            "active when you move between documents. App Theme and Dark Editor "
            "are independent: Light, Dark or System changes application chrome, "
            "while Dark Editor controls the source and preview canvas.</p>"
            "<p><b>Ctrl+Shift+[</b> opens Source Font and <b>Ctrl+Shift+]</b> opens "
            "Preview Font. <b>Ctrl+F</b> opens document Find while editing (press it again while Find has focus to close), and "
            "focuses the active Dashboard or folder search box in navigation "
            "contexts.</p>",
        )
        add_page(
            "Save safely",
            "MaqaronyDesk edits your Markdown files directly.",
            "<p><b>Save</b> writes the active document. Save and New, Save and "
            "Dashboard, and Save and Exit save first, then perform the named "
            "action.</p>"
            "<p>If another program changes an open file, MaqaronyDesk checks the "
            "on-disk content before overwriting it and asks what to do when the "
            "contents genuinely differ.</p>",
        )
        shortcuts_button = QPushButton("Open Keyboard Shortcuts…", wizard)
        shortcuts_button.setAutoDefault(False)
        shortcuts_button.clicked.connect(self._show_shortcuts)
        add_page(
            "Drag, drop and help",
            "External file drops are import-only.",
            "<p><b>Settings</b> contains application theme, Dashboard, launch-"
            "screen, tab, and file-handling choices. App Launch Screen defaults "
            "to Dashboard; Last File reopens the active Workspace's most recently "
            "opened valid file.</p>"
            "<p>Drag external Markdown files onto the Dashboard, workspace tree, "
            "or Folder Dashboard to import them into that target. Imported files "
            "stay closed until you choose to open or manage them.</p>"
            "<p>Help contains the bundled documentation, this Quick Tour, the "
            "live keyboard-shortcut inventory, the MaqaronyDesk GitHub repository, "
            "issue reporting and About.</p>",
            shortcuts_button,
        )

        def tour_finished(_result: int) -> None:
            self.quick_tour_dialog = None
            page = self._current_page()
            if page is not None:
                QTimer.singleShot(
                    0,
                    (page.preview if page.view_mode == "preview" else page.editor).setFocus,
                )

        wizard.finished.connect(tour_finished)
        self.quick_tour_dialog = wizard
        wizard.show()
        wizard.raise_()
        wizard.activateWindow()

    # -- x13.3 extraction boundary between original method groups --
    def _open_documentation(self) -> None:
        readme = self.runtime_paths.package_root / "docs" / "README.md"
        if not readme.is_file():
            QMessageBox.information(
                self,
                "Documentation — MaqaronyDesk",
                "The bundled MaqaronyDesk Markdown documentation could not be found.",
            )
            return
        self._launch_new_window(readme)

    def _shortcut_catalog(self) -> dict[str, list[tuple[str, QAction | str]]]:
        """Return every assigned shortcut, grouped by the live AppMenu taxonomy.

        AppMenu actions are collected recursively so nested menu commands stay
        synchronized with the Keyboard Shortcuts dialog automatically. Only
        shortcuts that intentionally have no AppMenu QAction are appended
        explicitly below.
        """
        label_overrides = {
            self.rename_file_action: "Rename File or Folder",
        }

        def collect(menu: QMenu) -> list[tuple[str, QAction | str]]:
            entries: list[tuple[str, QAction | str]] = []
            for action in menu.actions():
                submenu = action.menu()
                if submenu is not None:
                    entries.extend(collect(submenu))
                    continue
                if action.shortcut().toString(
                    QKeySequence.SequenceFormat.NativeText
                ).strip():
                    entries.append((label_overrides.get(action, action.text()), action))
            return entries

        catalog: dict[str, list[tuple[str, QAction | str]]] = {
            "File": collect(self.file_menu),
            "Edit": collect(self.edit_menu),
            "Markdown": collect(self.markdown_menu),
            "Insert": collect(self.insert_menu),
            "View": collect(self.view_menu),
            "Settings": collect(self.settings_menu),
            "Help": collect(self.help_menu),
        }

        # These shortcuts are intentionally not represented by AppMenu QActions.
        catalog["File"].extend((
            ("Close Tab / Dashboard", self.close_context_action),
            ("Open Context Tab", self.open_context_tab_action),
        ))
        catalog["Edit"].extend((
            ("Find Next", "F3"),
            ("Find Previous", "Shift+F3"),
            ("Clear Search", "Esc"),
            ("Toggle Overwrite Mode", "Insert"),
        ))
        catalog["View"].extend((
            (("Next Document Tab" if self._tabs_enabled() else "Next Ribbon Tab"), self.next_document_tab_action),
            (("Previous Document Tab" if self._tabs_enabled() else "Previous Ribbon Tab"), self.previous_document_tab_action),
        ))
        catalog["Settings"].extend((
            ("Toggle List/Grid View", self.toggle_dashboard_view_action),
            ("Toggle Sidebar Position", self.toggle_sidebar_position_action),
        ))
        return catalog

    def _show_shortcuts(self) -> None:
        if self.shortcuts_dialog is not None:
            self.shortcuts_dialog.show()
            self.shortcuts_dialog.raise_()
            self.shortcuts_dialog.activateWindow()
            return
        dialog = ShortcutsDialog(self._shortcut_catalog(), self)
        dialog.finished.connect(
            lambda _result: setattr(self, "shortcuts_dialog", None)
        )
        self.shortcuts_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog.search.setFocus(Qt.FocusReason.ShortcutFocusReason)


    def _open_github(self) -> None:
        self.desktop_launcher.open_url(GITHUB_URL)

    def _open_issues(self) -> None:
        self.desktop_launcher.open_url(ISSUES_URL)

    def _show_about_dialog(self) -> None:
        if self.about_dialog is not None:
            self.about_dialog.show()
            self.about_dialog.raise_()
            self.about_dialog.activateWindow()
            return

        about_icon = self.package_root / "assets" / "icons" / "maqaronydesk-about.png"
        dialog = AboutDialog(
            about_icon if about_icon.is_file() else self.icon_path,
            self.runtime_paths.config_path,
            self,
            desktop_launcher=self.desktop_launcher,
        )
        dialog.finished.connect(
            lambda _result: setattr(self, "about_dialog", None)
        )
        self.about_dialog = dialog
        dialog.show()

