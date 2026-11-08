"""Existing x8 command and appearance methods; definitions relocated unchanged."""
from __future__ import annotations

from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PyQt6.QtWidgets import QApplication, QMenu
from maqarony_desk.widgets.editor_page import EditorPage
from maqarony_desk.widgets.theme import apply_theme, effective_scheme

class EditorCommandsAppearanceMixin:

    def _add_action(self, menu, text, slot, shortcut=None, *, checkable=False):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.setCheckable(checkable)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _command(self, text, slot=None, shortcut=None, *, checkable=False) -> QAction:
        action = QAction(text, self)
        if slot is not None:
            action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut) if isinstance(shortcut, str) else shortcut)
        action.setCheckable(checkable)
        label = text.replace("&", "").replace("…", "...").strip()
        shortcut_text = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        action.setToolTip(f"{label} — {shortcut_text}" if shortcut_text else label)
        return action

    def _build_menu_bar(self) -> None:
        # MaqaronyPad's command language, adapted only where the workspace
        # genuinely has a different file/workspace operation.
        self.new_action = self._command("New File…", self._new_markdown_file, QKeySequence.StandardKey.New)
        self.new_window_action = self._command("New Window…", self._new_window, "Ctrl+Alt+Shift+N")
        self.new_folder_action = self._command("New Folder…", self._new_folder, "Ctrl+Shift+N")
        self.manage_workspaces_action = self._command("Open / Manage Workspaces...", self._show_projects, "Ctrl+O")
        self.import_file_action = self._command("Import File into Workspace...", self._import_file_into_workspace, "Ctrl+Alt+Shift+I")
        self.open_external_file_action = self._command("Open External File...", self._open_external_file, "Ctrl+Alt+Shift+O")
        self.refresh_workspace_action = self._command("Refresh Workspace", self._refresh_workspace, "Ctrl+Shift+F5")
        self.save_action = self._command("Save", self._save_current, QKeySequence.StandardKey.Save)
        self.save_as_action = self._command("Save As…", self._save_current_as)
        self.save_new_action = self._command("Save and New", self._save_and_new, "Ctrl+Shift+S")
        self.save_dashboard_action = self._command("Save and Dashboard", self._save_and_dashboard, "Ctrl+Shift+W")
        self.save_exit_action = self._command("Save and Exit", self._save_and_exit, "Ctrl+Shift+Q")
        self.duplicate_action = self._command("Duplicate File…", self._duplicate_current, "Ctrl+Shift+D")
        self.rename_file_action = self._command("Rename File…", self._rename_current, "F2")
        self.delete_file_action = self._command("Delete File", self._delete_current_file)
        self.open_document_folder_action = self._command("Open Containing Folder", self._open_current_document_folder, "Ctrl+Shift+O")
        self.external_editor_action = self._command("Open in External Editor", self._open_current_external, "Ctrl+Shift+E")
        self.properties_action = self._command("Properties", self._show_properties, "F4")
        self.print_action = self._command("Print…", self._print_current, QKeySequence.StandardKey.Print)
        self.export_pdf_action = self._command("Export PDF…", self._export_pdf_current, "Ctrl+Shift+P")
        self.exit_action = self._command("Exit", self.close, QKeySequence.StandardKey.Quit)

        self.undo_action = self._command("Undo", self._undo, QKeySequence.StandardKey.Undo)
        self.redo_action = self._command("Redo", self._redo, "Ctrl+Y")
        self.cut_action = self._command("Cut", self._cut, QKeySequence.StandardKey.Cut)
        self.copy_action = self._command("Copy", self._copy, QKeySequence.StandardKey.Copy)
        self.paste_action = self._command("Paste", self._paste, QKeySequence.StandardKey.Paste)
        self.paste_plain_action = self._command("Paste as Plain Text", self._paste_plain_text, "Ctrl+Shift+V")
        self.delete_text_action = self._command("Delete", self._delete_text, "Delete")
        self.duplicate_line_action = self._command("Duplicate Line / Selection", self._duplicate_line, "Ctrl+D")
        self.delete_line_action = self._command("Delete Line", self._delete_line, "Ctrl+Shift+K")
        self.select_all_action = self._command("Select All", self._select_all, QKeySequence.StandardKey.SelectAll)
        self.comment_action = self._command("Toggle Comment", self._toggle_comment, "Ctrl+/")
        self.find_action = self._command("Find", self._focus_find, QKeySequence.StandardKey.Find)
        self.replace_action = self._command("Find and Replace", self._focus_replace, "Ctrl+H")
        self.goto_action = self._command("Go To Line...", self._go_to_line, "Ctrl+G")

        self.bold_action = self._command("Bold", lambda: self._editor_call("toggle_bold"), "Ctrl+B")
        self.italic_action = self._command("Italic", lambda: self._editor_call("toggle_italic"), "Ctrl+I")
        self.strike_action = self._command("Strikethrough", lambda: self._editor_call("toggle_strikethrough"), "Ctrl+Shift+X")
        self.quote_action = self._command("Quote Block\t>", lambda: self._editor_call("toggle_blockquote"))
        self.bullet_action = self._command("Bullet List", lambda: self._editor_call("toggle_bullet_list"), "Ctrl+L")
        self.number_action = self._command("Numbered List", lambda: self._editor_call("toggle_numbered_list"), "Ctrl+Shift+L")
        self.task_action = self._command("Task List", lambda: self._editor_call("toggle_task_list"))
        self.indent_action = self._command("Indent", lambda: self._editor_call("indent_selection_or_insert_spaces"), "Ctrl+]")
        self.outdent_action = self._command("Outdent", lambda: self._editor_call("unindent_selection_or_line"), "Ctrl+[")
        self.inline_code_action = self._command("Inline Code", lambda: self._editor_call("toggle_inline_code"), "Ctrl+`")
        self.code_fence_action = self._command("Code Block\t```", self._insert_code_block)
        self.heading_actions = []
        for level in range(0, 7):
            label = "Normal Paragraph" if level == 0 else f"Heading {level}"
            self.heading_actions.append(self._command(label, lambda _checked=False, n=level: self._editor_call("apply_heading", n), f"Ctrl+Shift+{level}"))
        self.heading_tabbed_action = QAction("Heading", self)
        heading_menu = QMenu(self)
        for action in self.heading_actions: heading_menu.addAction(action)
        self.heading_tabbed_action.setMenu(heading_menu)

        self.code_tabbed_action = QAction("Code", self)
        code_menu = QMenu(self)
        code_menu.addAction(self.inline_code_action)
        code_menu.addAction(self.code_fence_action)
        self.code_tabbed_action.setMenu(code_menu)

        self.link_action = self._command("Insert Link…", self._insert_link, "Ctrl+K")
        self.edit_link_action = self._command("Edit Link…", self._edit_link)
        self.remove_link_action = self._command("Remove Link", self._remove_link)
        self.rule_action = self._command("Horizontal Rule", lambda: self._editor_call("insert_horizontal_rule"), "Ctrl+Shift+H")
        self.image_action = self._command("Image Reference…", self._insert_image, "Ctrl+Shift+I")
        self.table_action = self._command("Table…", self._insert_table, "Ctrl+Shift+T")
        self.date_time_action = self._command("Date and Time", lambda: self._insert_text(datetime.now().strftime("%Y-%m-%d %H:%M")), "F5")
        self.date_action = self._command("Date Only", lambda: self._insert_text(datetime.now().strftime("%Y-%m-%d")), "Ctrl+;")
        self.time_action = self._command("Time Only", lambda: self._insert_text(datetime.now().strftime("%H:%M")), "Ctrl+:")
        self.symbol_action = self._command("Symbol…", self._insert_symbol, "Shift+F5")
        self.link_tabbed_action = QAction("Link", self)
        link_tabbed_menu = QMenu(self)
        link_tabbed_menu.addAction(self.link_action)
        link_tabbed_menu.addAction(self.edit_link_action)
        link_tabbed_menu.addSeparator()
        link_tabbed_menu.addAction(self.remove_link_action)
        self.link_tabbed_action.setMenu(link_tabbed_menu)

        self.source_only_action = self._command("Source Only", lambda: self._set_document_view("source"), "Ctrl+1", checkable=True)
        self.split_action = self._command("Source + Preview", lambda: self._set_document_view("split"), "Ctrl+2", checkable=True)
        self.preview_only_action = self._command("Preview Only", lambda: self._set_document_view("preview"), "Ctrl+3", checkable=True)
        view_group = QActionGroup(self); view_group.setExclusive(True)
        for action in (self.source_only_action, self.split_action, self.preview_only_action): view_group.addAction(action)
        self.view_only_action = self._command("Locked Mode", self._toggle_lock_editor_current, "F12", checkable=True)
        self.word_wrap_action = self._command("Word Wrap", self._toggle_word_wrap, "Ctrl+Alt+Shift+W", checkable=True)
        self.line_numbers_action = self._command("Line Numbers", self._toggle_line_numbers, "Ctrl+Alt+Shift+L", checkable=True)
        canvas_light = self.config.get("editor_canvas_light", True)
        if not isinstance(canvas_light, bool):
            canvas_light = True
        self.editor_canvas_theme_action = self._command(
            "Dark Editor", self._toggle_editor_canvas_light,
            "Ctrl+Alt+Shift+E", checkable=True,
        )
        self.editor_canvas_theme_action.setChecked(not canvas_light)
        self.status_bar_action = self._command(
            "Show Status", self._toggle_status_bar,
            "Ctrl+Alt+Shift+S", checkable=True,
        )
        self.status_bar_action.setChecked(bool(self.config.get("show_status_bar", True)))
        self.statusBar().setVisible(self.status_bar_action.isChecked())
        self.file_header_action = self._command("File Header", self._toggle_file_header, "Ctrl+Alt+Shift+F", checkable=True)
        self.file_header_action.setChecked(bool(self.config.get("show_file_header", True)))
        self.collapsed_mode_action = self._command("Focused Mode", self._toggle_collapsed_mode, "F10", checkable=True)
        self.zoom_in_action = self._command("Zoom In", lambda: self._zoom_current(1), QKeySequence.StandardKey.ZoomIn)
        self.zoom_out_action = self._command("Zoom Out", lambda: self._zoom_current(-1), QKeySequence.StandardKey.ZoomOut)
        self.zoom_reset_action = self._command("Reset Zoom", self._zoom_reset, "Ctrl+0")
        self.display_font_action = self._command("Source Font…", self._choose_display_font, "Ctrl+Shift+[")
        self.preview_font_action = self._command("Preview Font…", self._choose_preview_font, "Ctrl+Shift+]")
        self.tab_width_action = self._command("Tab Width…", self._choose_tab_width)

        self.dashboard_action = self._command("Dashboard", self.editor_manager.show_dashboard)
        # Context-sensitive tab/navigation shortcuts are window-owned rather
        # than attached to the Dashboard or Markdown actions.
        self.close_context_action = self._command(
            "Close Tab / Dashboard", self._close_context, "Ctrl+W"
        )
        self.open_context_tab_action = self._command(
            "Open Context Tab", self._open_context_tab, "Ctrl+T"
        )
        self.addAction(self.close_context_action)
        self.addAction(self.open_context_tab_action)
        self.list_action = self._command("List View", lambda: self.editor_manager.set_view_mode("list"), checkable=True)
        self.grid_action = self._command("Grid View", lambda: self.editor_manager.set_view_mode("grid"), checkable=True)
        self.list_action.setToolTip("Dashboard — List View")
        self.grid_action.setToolTip("Dashboard — Grid View")
        self.toggle_dashboard_view_action = self._command(
            "Toggle List/Grid View", self._toggle_dashboard_view,
            "Ctrl+Alt+Shift+V",
        )
        dashboard_view_group = QActionGroup(self); dashboard_view_group.setExclusive(True)
        dashboard_view_group.addAction(self.list_action); dashboard_view_group.addAction(self.grid_action)
        self.sidebar_action = self._command("Show Sidebar", self._toggle_sidebar, "F9", checkable=True); self.sidebar_action.setChecked(True)
        sidebar_position = str(self.config.get("sidebar_position", "left"))
        if sidebar_position not in {"left", "right"}:
            sidebar_position = "left"
        self.sidebar_position_actions: dict[str, QAction] = {}
        sidebar_position_group = QActionGroup(self)
        sidebar_position_group.setExclusive(True)
        for value, label in (("left", "Dock to Left"), ("right", "Dock to Right")):
            action = self._command(
                label,
                lambda _checked=False, selected=value: self._set_sidebar_position(selected),
                checkable=True,
            )
            action.setChecked(value == sidebar_position)
            sidebar_position_group.addAction(action)
            self.sidebar_position_actions[value] = action
        self.left_sidebar_action = self.sidebar_position_actions["left"]
        self.right_sidebar_action = self.sidebar_position_actions["right"]
        self.left_sidebar_action.setToolTip("Sidebar — Dock to Left")
        self.right_sidebar_action.setToolTip("Sidebar — Dock to Right")
        self.toggle_sidebar_position_action = self._command(
            "Toggle Sidebar Position", self._toggle_sidebar_position, "Shift+F9"
        )
        self.addAction(self.toggle_sidebar_position_action)
        self.fullscreen_action = self._command("Full Screen", self._toggle_fullscreen, "F11", checkable=True)
        self.theme_system_action = self._command("System", lambda: self._set_theme("system"), checkable=True)
        self.theme_dark_action = self._command("Dark", lambda: self._set_theme("dark"), checkable=True)
        self.theme_light_action = self._command("Light", lambda: self._set_theme("light"), checkable=True)
        self.theme_light_action.setToolTip("Theme — Light")
        self.theme_dark_action.setToolTip("Theme — Dark")
        self.theme_system_action.setToolTip("Theme — System")
        self.icon_family_actions = {}
        icon_group = QActionGroup(self); icon_group.setExclusive(True)
        for family, label in (
            ("harmony", "Maqa Icons Harmony"),
            ("humility", "Maqa Icons Humility"),
            ("heritage", "Maqa Icons Heritage"),
            ("halcyon", "Maqa Icons Halcyon"),
        ):
            action = self._command(
                label, lambda _checked=False, selected=family: self._set_icon_family(selected),
                checkable=True,
            )
            action.setToolTip(label)
            action.setChecked(family == self.icon_family)
            icon_group.addAction(action)
            self.icon_family_actions[family] = action
        self.icon_harmony_action = self.icon_family_actions["harmony"]
        self.icon_humility_action = self.icon_family_actions["humility"]
        self.icon_heritage_action = self.icon_family_actions["heritage"]
        self.icon_halcyon_action = self.icon_family_actions["halcyon"]
        theme_group = QActionGroup(self); theme_group.setExclusive(True)
        for action in (self.theme_light_action, self.theme_dark_action, self.theme_system_action): theme_group.addAction(action)
        current_theme = str(self.config.get("app_theme", "light"))
        {"system": self.theme_system_action, "dark": self.theme_dark_action, "light": self.theme_light_action}.get(current_theme, self.theme_system_action).setChecked(True)

        self.app_launch_screen = str(
            self.config.get("app_launch_screen", "dashboard")
        )
        if self.app_launch_screen not in {"dashboard", "last_file"}:
            self.app_launch_screen = "dashboard"
        self.launch_dashboard_action = self._command(
            "Dashboard",
            lambda: self._set_app_launch_screen("dashboard"),
            checkable=True,
        )
        self.launch_last_file_action = self._command(
            "Last File",
            lambda: self._set_app_launch_screen("last_file"),
            checkable=True,
        )
        launch_screen_group = QActionGroup(self)
        launch_screen_group.setExclusive(True)
        launch_screen_group.addAction(self.launch_dashboard_action)
        launch_screen_group.addAction(self.launch_last_file_action)
        self.launch_dashboard_action.setChecked(
            self.app_launch_screen == "dashboard"
        )
        self.launch_last_file_action.setChecked(
            self.app_launch_screen == "last_file"
        )
        self.launch_dashboard_action.setToolTip("Launch Screen — Dashboard")
        self.launch_last_file_action.setToolTip("Launch Screen — Last File")

        tabs_enabled = bool(self.config.get("tabs_enabled", True))
        self.tabs_actions: dict[str, QAction] = {}
        tabs_group = QActionGroup(self)
        tabs_group.setExclusive(True)
        for value, label in (
            (True, "Tabs Enabled"),
            (False, "Tabs Disabled"),
        ):
            action = self._command(
                label,
                lambda _checked=False, enabled=value: self._set_tabs_enabled(enabled),
                (None if value else "Ctrl+Alt+Shift+T"),
                checkable=True,
            )
            action.setChecked(value == tabs_enabled)
            tabs_group.addAction(action)
            self.tabs_actions["enabled" if value else "disabled"] = action
        self.tabs_enabled_action = self.tabs_actions["enabled"]
        self.tabs_disabled_action = self.tabs_actions["disabled"]
        self.tabs_enabled_action.setToolTip("File Launch — Tabs Enabled")
        self.tabs_disabled_action.setToolTip("File Launch — Tabs Disabled")
        self.app_tabs_toggle_action = self._command(
            "Tabs Enabled / Disabled", self._toggle_tabs_mode
        )

        duplicate_policy = str(self.config.get("dirty_duplicate_action", "ask")).lower()
        if duplicate_policy not in {"ask", "current", "saved"}:
            duplicate_policy = "ask"
        self.dirty_duplicate_actions: dict[str, QAction] = {}
        dirty_duplicate_group = QActionGroup(self)
        dirty_duplicate_group.setExclusive(True)
        for value, label in (
            ("ask", "Ask Every Time"),
            ("current", "Duplicate Current Document"),
            ("saved", "Duplicate Last Saved Version"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_dirty_duplicate_action(selected),
                checkable=True,
            )
            action.setChecked(value == duplicate_policy)
            dirty_duplicate_group.addAction(action)
            self.dirty_duplicate_actions[value] = action

        external_policy = str(self.config.get("dirty_external_action", "ask")).lower()
        if external_policy not in {"ask", "save", "saved"}:
            external_policy = "ask"
        self.dirty_external_actions: dict[str, QAction] = {}
        dirty_external_group = QActionGroup(self)
        dirty_external_group.setExclusive(True)
        for value, label in (
            ("ask", "Ask Every Time"),
            ("save", "Save Changes and Open"),
            ("saved", "Open Last Saved Version"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_dirty_external_action(selected),
                checkable=True,
            )
            action.setChecked(value == external_policy)
            dirty_external_group.addAction(action)
            self.dirty_external_actions[value] = action

        self.next_document_tab_action = self._command("Next Tab", lambda: self._cycle_context_tab(1), "Ctrl+Tab")
        self.previous_document_tab_action = self._command("Previous Tab", lambda: self._cycle_context_tab(-1), "Ctrl+Shift+Tab")
        self.previous_file_action = self._command("Previous File", lambda: self.navigation.navigate_adjacent_module(-1), "Ctrl+Up")
        self.next_file_action = self._command("Next File", lambda: self.navigation.navigate_adjacent_module(1), "Ctrl+Down")
        for action in (self.next_document_tab_action, self.previous_document_tab_action, self.previous_file_action, self.next_file_action, self.toggle_dashboard_view_action):
            self.addAction(action)

        self.docs_action = self._command("Documentation", self._open_documentation, QKeySequence.StandardKey.HelpContents)
        self.shortcuts_action = self._command("Keyboard Shortcuts", self._show_shortcuts, "Ctrl+Shift+/")
        self.quick_start_action = self._command("Quick Tour…", self._show_quick_tour, "Shift+F1")
        self.quick_start_action.setToolTip("Quick Tour… — Shift+F1")
        self.github_action = self._command("GitHub Repository", self._open_github)
        self.issue_action = self._command("Raise an Issue", self._open_issues)
        self.about_action = self._command("About MaqaronyDesk", self._show_about_dialog); self.about_action.setMenuRole(QAction.MenuRole.AboutRole)

        bar = self.menuBar()
        bar.setNativeMenuBar(True)
        self.file_menu = bar.addMenu("&File")
        file_menu = self.file_menu
        for action in (self.new_action, self.new_folder_action): file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(self.dashboard_action)
        file_menu.addAction(self.next_file_action)
        file_menu.addAction(self.previous_file_action)
        file_menu.addSeparator()
        file_menu.addAction(self.refresh_workspace_action)
        self.workspace_menu = file_menu.addMenu("Workspace(s)")
        self.workspace_tabbed_action = self.workspace_menu.menuAction()
        self.workspace_action_group = QActionGroup(self.workspace_menu)
        self.workspace_action_group.setExclusive(True)
        self.workspace_menu.aboutToShow.connect(self._rebuild_workspace_menu)
        self._rebuild_workspace_menu()
        file_menu.addAction(self.import_file_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_external_file_action)
        file_menu.addAction(self.new_window_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action); file_menu.addAction(self.save_as_action); file_menu.addAction(self.save_new_action); file_menu.addAction(self.save_dashboard_action)
        more = file_menu.addMenu("More Actions")
        for action in (self.duplicate_action, self.rename_file_action, self.delete_file_action): more.addAction(action)
        more.addSeparator()
        more.addAction(self.external_editor_action)
        more.addAction(self.open_document_folder_action)
        more.addSeparator()
        more.addAction(self.properties_action)
        file_menu.addSeparator(); file_menu.addAction(self.print_action); file_menu.addAction(self.export_pdf_action)
        file_menu.addSeparator(); file_menu.addAction(self.exit_action); file_menu.addAction(self.save_exit_action)

        self.edit_menu = bar.addMenu("&Edit")
        edit = self.edit_menu
        edit.addAction(self.undo_action); edit.addAction(self.redo_action); edit.addSeparator()
        for action in (self.cut_action, self.copy_action, self.paste_action, self.paste_plain_action): edit.addAction(action)
        edit.addSeparator(); edit.addAction(self.delete_text_action); edit.addSeparator()
        edit.addAction(self.comment_action)
        edit.addAction(self.duplicate_line_action); edit.addAction(self.delete_line_action); edit.addSeparator(); edit.addAction(self.select_all_action)
        edit.addSeparator(); edit.addAction(self.find_action); edit.addAction(self.goto_action); edit.addAction(self.replace_action)

        self.markdown_menu = bar.addMenu("&Markdown")
        markdown = self.markdown_menu
        for action in (self.bold_action, self.italic_action, self.strike_action, self.quote_action): markdown.addAction(action)
        markdown.addSeparator()
        for action in (self.bullet_action, self.number_action, self.task_action): markdown.addAction(action)
        markdown.addSeparator(); markdown.addAction(self.indent_action); markdown.addAction(self.outdent_action)
        markdown.addSeparator(); markdown.addAction(self.inline_code_action); markdown.addAction(self.code_fence_action)
        markdown.addSeparator()
        headings = markdown.addMenu("Heading")
        for action in self.heading_actions: headings.addAction(action)
        self.heading_menu_action = headings.menuAction()

        self.insert_menu = bar.addMenu("&Insert")
        insert = self.insert_menu
        insert.addAction(self.image_action)
        links = insert.addMenu("Link"); links.addAction(self.link_action); links.addAction(self.edit_link_action); links.addSeparator(); links.addAction(self.remove_link_action)
        self.link_menu_action = links.menuAction()
        insert.addSeparator()
        insert.addAction(self.table_action)
        insert.addSeparator()
        for action in (self.date_time_action, self.date_action, self.time_action): insert.addAction(action)
        insert.addSeparator()
        insert.addAction(self.rule_action); insert.addAction(self.symbol_action)

        self.view_menu = bar.addMenu("&View")
        view = self.view_menu
        view.addAction(self.fullscreen_action)
        view.addAction(self.status_bar_action)
        view.addSeparator()
        view.addAction(self.word_wrap_action)
        view.addAction(self.line_numbers_action)
        view.addAction(self.editor_canvas_theme_action)
        view.addSeparator()
        view.addAction(self.view_only_action)
        layout_menu = view.addMenu("Editor Layout")
        layout_menu.addAction(self.file_header_action)
        layout_menu.addSeparator()
        layout_menu.addAction(self.source_only_action)
        layout_menu.addAction(self.split_action)
        layout_menu.addAction(self.preview_only_action)
        self.editor_layout_menu_action = layout_menu.menuAction()
        view.addSeparator()
        zoom = view.addMenu("Editor Zoom")
        zoom.addAction(self.zoom_in_action)
        zoom.addAction(self.zoom_out_action)
        zoom.addSeparator()
        zoom.addAction(self.zoom_reset_action)
        more_settings = view.addMenu("Editor Miscellaneous")
        more_settings.addAction(self.tab_width_action)
        more_settings.addSeparator()
        more_settings.addAction(self.display_font_action)
        more_settings.addAction(self.preview_font_action)

        self.settings_menu = bar.addMenu("&Settings")
        settings = self.settings_menu
        settings.addAction(self.collapsed_mode_action)
        settings.addSeparator()
        theme_menu = settings.addMenu("App Theme")
        theme_menu.addAction(self.theme_light_action)
        theme_menu.addAction(self.theme_dark_action)
        theme_menu.addAction(self.theme_system_action)
        self.theme_tabbed_action = theme_menu.menuAction()
        icon_menu = settings.addMenu("App Icons")
        for family in ("harmony", "humility", "heritage", "halcyon"):
            icon_menu.addAction(self.icon_family_actions[family])
        self.app_icons_menu_action = icon_menu.menuAction()
        dashboard_menu = settings.addMenu("App Dashboard")
        dashboard_menu.addAction(self.list_action)
        dashboard_menu.addAction(self.grid_action)
        self.dashboard_tabbed_action = dashboard_menu.menuAction()
        sidebar_menu = settings.addMenu("App Sidebar")
        sidebar_menu.addAction(self.sidebar_action)
        sidebar_menu.addSeparator()
        sidebar_menu.addAction(self.left_sidebar_action)
        sidebar_menu.addAction(self.right_sidebar_action)
        self.app_sidebar_menu_action = sidebar_menu.menuAction()
        settings.addSeparator()
        launch_screen_menu = settings.addMenu("App Launch Screen")
        launch_screen_menu.addAction(self.launch_dashboard_action)
        launch_screen_menu.addAction(self.launch_last_file_action)
        self.launch_screen_tabbed_action = launch_screen_menu.menuAction()
        file_launch_menu = settings.addMenu("App File Launch")
        file_launch_menu.addAction(self.tabs_enabled_action)
        file_launch_menu.addAction(self.tabs_disabled_action)
        self.app_file_launch_menu_action = file_launch_menu.menuAction()
        settings.addSeparator()
        dirty_duplicate_menu = settings.addMenu("Duplicate File with Unsaved Changes")
        for key in ("ask", "current", "saved"):
            dirty_duplicate_menu.addAction(self.dirty_duplicate_actions[key])
        self.dirty_duplicate_tabbed_action = dirty_duplicate_menu.menuAction()
        dirty_external_menu = settings.addMenu("Open Externally with Unsaved Changes")
        for key in ("ask", "save", "saved"):
            dirty_external_menu.addAction(self.dirty_external_actions[key])
        self.dirty_external_tabbed_action = dirty_external_menu.menuAction()

        self.help_menu = bar.addMenu("&Help")
        help_menu = self.help_menu
        help_menu.addAction(self.docs_action)
        help_menu.addSeparator()
        help_menu.addAction(self.quick_start_action); help_menu.addAction(self.shortcuts_action)
        help_menu.addSeparator()
        help_menu.addAction(self.github_action); help_menu.addAction(self.issue_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)
        self._refresh_action_icons()

    def _toolbar_icon_path(self, name: str) -> Path:
        family_dir = {
            "harmony": "toolbar-icons", "humility": "toolbar-icons-classic",
            "heritage": "toolbar-icons-original", "halcyon": "toolbar-icons-aero",
        }[self.icon_family]
        return self.package_root / "assets" / family_dir / effective_scheme(str(self.config.get("app_theme", "light"))) / f"{name}.png"

    def _sidebar_toggle_icon_name(self) -> str:
        """The QAction belongs to both AppMenu and Ribbon; derive its icon from docking."""
        if all(hasattr(self, name) for name in ("splitter", "navigation", "content_host")):
            position = self._sidebar_position()
        else:
            position = str(self.config.get("sidebar_position", "left"))
        return "show-sidebar-right" if position == "right" else "show-sidebar"

    def _refresh_sidebar_toggle_icon(self) -> None:
        """Change only icon artwork, never the visibility/check state of Show Sidebar."""
        path = self._toolbar_icon_path(self._sidebar_toggle_icon_name())
        self.sidebar_action.setIcon(QIcon(str(path)) if path.is_file() else QIcon())

    def _refresh_action_icons(self) -> None:
        mapping = {
            "new_action":"new", "new_window_action":"new-window", "new_folder_action":"new-folder", "dashboard_action":"show-dashboard", "workspace_tabbed_action":"manage-workspaces", "import_file_action":"import-file", "open_external_file_action":"open", "previous_file_action":"previous", "next_file_action":"next", "save_action":"save", "save_as_action":"save-as", "save_new_action":"save-new", "save_dashboard_action":"save-dashboard", "save_exit_action":"save-exit",
            "duplicate_action":"duplicate-file", "rename_file_action":"rename", "delete_file_action":"delete-file", "open_document_folder_action":"open-folder", "external_editor_action":"external-editor", "properties_action":"properties",
            "print_action":"print", "export_pdf_action":"export-pdf", "exit_action":"exit", "undo_action":"undo", "redo_action":"redo", "cut_action":"cut", "copy_action":"copy", "paste_action":"paste", "paste_plain_action":"paste-plain", "delete_text_action":"delete-text", "comment_action":"comment-toggle", "select_all_action":"select-all", "duplicate_line_action":"duplicate-line", "delete_line_action":"delete-line", "find_action":"find", "replace_action":"replace", "goto_action":"goto-line",
            "bold_action":"bold", "italic_action":"italic", "strike_action":"strikethrough", "quote_action":"quote-block", "bullet_action":"bullet-list", "number_action":"numbered-list", "task_action":"task-list", "indent_action":"indent", "outdent_action":"outdent", "inline_code_action":"inline-code", "code_fence_action":"code-block", "link_action":"insert-link", "edit_link_action":"edit-link", "remove_link_action":"remove-link", "rule_action":"horizontal-rule", "image_action":"insert-image", "table_action":"insert-table", "date_time_action":"date-time", "date_action":"insert-date", "time_action":"insert-time", "symbol_action":"symbols",
            "fullscreen_action":"full-screen", "file_header_action":"file-header", "collapsed_mode_action":"focused-mode", "sidebar_action":self._sidebar_toggle_icon_name(), "left_sidebar_action":"dock-left", "right_sidebar_action":"dock-right", "source_only_action":"source-only", "split_action":"source-preview", "preview_only_action":"preview-only", "view_only_action":"view-only", "word_wrap_action":"word-wrap", "line_numbers_action":"line-numbers", "editor_canvas_theme_action":"editor-canvas", "status_bar_action":"status-bar", "zoom_in_action":"zoom-in", "zoom_out_action":"zoom-out", "zoom_reset_action":"zoom-reset", "display_font_action":"default-font", "preview_font_action":"font-dialog", "tab_width_action":"tab-width",
            "app_icons_menu_action":"app-icons", "icon_harmony_action":"icons-new",
            "icon_humility_action":"icons-classic", "icon_heritage_action":"icons-legacy",
            "theme_tabbed_action":"app-theme", "dashboard_tabbed_action":"app-dashboard", "app_sidebar_menu_action":"sidebar-settings", "launch_screen_tabbed_action":"app-launch-screen", "app_file_launch_menu_action":"file-launch", "tabs_enabled_action":"tabs-enabled", "tabs_disabled_action":"tabs-disabled", "editor_layout_menu_action":"layout-markdown", "dirty_duplicate_tabbed_action":"dirty-duplicate-policy", "dirty_external_tabbed_action":"dirty-external-policy",
            "theme_system_action":"theme-system", "theme_dark_action":"theme-dark", "theme_light_action":"theme-light", "list_action":"list-view", "grid_action":"grid-view", "launch_dashboard_action":"launch-dashboard", "launch_last_file_action":"launch-last-file", "heading_tabbed_action":"heading-group", "heading_menu_action":"heading-group", "code_tabbed_action":"code-group", "link_tabbed_action":"link-group", "link_menu_action":"link-group", "docs_action":"documentation", "quick_start_action":"tutorial", "shortcuts_action":"shortcuts", "github_action":"github", "issue_action":"issue", "about_action":"about",
        }
        for attr, name in mapping.items():
            action = getattr(self, attr, None); path = self._toolbar_icon_path(name)
            if action is not None and path.is_file(): action.setIcon(QIcon(str(path)))
        for level, action in enumerate(self.heading_actions):
            path = self._toolbar_icon_path(f"heading-{level}")
            if path.is_file(): action.setIcon(QIcon(str(path)))
        if hasattr(self, "app_tabs_toggle_action"):
            path = self._toolbar_icon_path("tabs-enabled" if self._tabs_enabled() else "tabs-disabled")
            if path.is_file(): self.app_tabs_toggle_action.setIcon(QIcon(str(path)))
        if hasattr(self, "shell_ribbon"):
            self.shell_ribbon.refresh_theme()

    def _set_icon_family(self, family: str) -> None:
        if family not in {"harmony", "humility", "heritage", "halcyon"}:
            return
        self.icon_family = family
        QApplication.instance().setProperty("maqa_icon_family", family)
        self.config.set("app_icon_family", family, save=True)
        self.icon_family_actions[family].setChecked(True)
        self._refresh_action_icons()
        self.editor_manager.dashboard.refresh_theme()
        for folder_page in self.editor_manager._folder_pages.values():
            folder_page.refresh_theme()
        self.show_status(f"Maqa Icons {family.title()}.")

    def _set_theme(self, theme: str) -> None:
        if theme not in {"system", "dark", "light"}:
            return
        # Application chrome is independent from the persisted Dark Editor choice.
        self.config.set("app_theme", theme, save=True)
        apply_theme(QApplication.instance(), theme)
        {"system": self.theme_system_action, "dark": self.theme_dark_action, "light": self.theme_light_action}[theme].setChecked(True)
        self._refresh_action_icons(); self.editor_manager.dashboard.refresh_theme()
        for folder_page in self.editor_manager._folder_pages.values(): folder_page.refresh_theme()
        for _path, state in tuple(self.states):
            if isinstance(state.editor_page, EditorPage):
                # Re-apply only the independent editor presentation through
                # the dirty-state-preserving path.
                state.editor_page.apply_canvas_theme()
        label = "System" if theme == "system" else theme.title()
        self.show_status(f"Theme: {label}.")

    def _toggle_editor_canvas_light(self, checked: bool) -> None:
        # 0.1.7 contract: application chrome and Markdown canvases are independent.
        # The action is named "Dark Editor": checked means both canvases are dark.
        self.config.set("editor_canvas_light", not bool(checked), save=True)
        self.editor_manager.apply_editor_theme()
        self.editor_manager.show_current_editor_status(
            "Editor canvas switched to a dark background."
            if bool(checked)
            else "Editor canvas switched to a light background.",
            4000,
        )

    def _choose_display_font(self) -> None:
        page = self._current_page()
        if page:
            page.choose_display_font()

    def _choose_preview_font(self) -> None:
        page = self._current_page()
        if page:
            page.choose_preview_font()

    def _sync_editor_view_actions(self) -> None:
        page = self._current_page()
        actions = (self.view_only_action, self.word_wrap_action, self.line_numbers_action, self.editor_canvas_theme_action, self.source_only_action, self.split_action, self.preview_only_action)
        for action in actions: action.blockSignals(True)
        self.view_only_action.setChecked(bool(page.view_only) if page else bool(self.config.get("lock_editor", False)))
        self.word_wrap_action.setChecked(bool(self.config.get("editor_word_wrap", True)))
        self.line_numbers_action.setChecked(bool(self.config.get("editor_line_numbers", True)))
        canvas_light = self.config.get("editor_canvas_light", True)
        if not isinstance(canvas_light, bool):
            canvas_light = True
        self.editor_canvas_theme_action.setChecked(not canvas_light)
        mode = page.view_mode if page else str(self.config.get("markopad_view_mode", "split"))
        self.source_only_action.setChecked(mode == "source")
        self.split_action.setChecked(mode == "split")
        self.preview_only_action.setChecked(mode == "preview")
        for action in actions: action.blockSignals(False)

    def _update_action_states(self, *_args) -> None:
        page = self._current_page()
        module = self._current_module()
        if page is not None and hasattr(self, "collapsed_mode_action") and self.collapsed_mode_action.isChecked():
            page.editor_status.setVisible(False)
            page.set_header_visible(False)
        editing = page is not None and module is not None
        document_actions = (
            self.save_action, self.save_as_action, self.save_new_action, self.save_dashboard_action, self.save_exit_action, self.undo_action, self.redo_action,
            self.cut_action, self.copy_action, self.paste_action, self.paste_plain_action,
            self.delete_text_action, self.duplicate_line_action, self.delete_line_action, self.comment_action, self.select_all_action,
            self.duplicate_action, self.delete_file_action, self.properties_action,
            self.external_editor_action, self.open_document_folder_action, self.print_action, self.export_pdf_action,
            self.replace_action, self.goto_action, self.view_only_action, self.word_wrap_action,
            self.line_numbers_action, self.display_font_action, self.preview_font_action, self.source_only_action, self.split_action,
            self.preview_only_action, self.zoom_in_action, self.zoom_out_action, self.zoom_reset_action,
            self.bold_action, self.italic_action, self.strike_action, self.quote_action, self.bullet_action,
            self.number_action, self.task_action, self.indent_action, self.outdent_action, self.inline_code_action,
            self.code_fence_action, self.heading_tabbed_action, self.link_action, self.edit_link_action,
            self.remove_link_action, self.rule_action, self.image_action, self.table_action, self.date_time_action,
            self.date_action, self.time_action, self.symbol_action,
        )
        for action in document_actions: action.setEnabled(editing)
        for action in self.heading_actions: action.setEnabled(editing)
        folder = self._selected_folder()
        self.rename_file_action.setEnabled(
            editing or (folder is not None and folder != self.library_root)
        )
        self._sync_editor_view_actions()
        if page:
            view_only = page.view_only
            source_active = self._source_interaction_active(page)
            self.undo_action.setEnabled(page.editor.document().isUndoAvailable() and not view_only and source_active)
            self.redo_action.setEnabled(page.editor.document().isRedoAvailable() and not view_only and source_active)
            mutable = not view_only and source_active
            for action in (self.cut_action, self.paste_action, self.paste_plain_action, self.delete_text_action, self.duplicate_line_action, self.delete_line_action, self.comment_action, self.bold_action, self.italic_action, self.strike_action, self.quote_action, self.bullet_action, self.number_action, self.task_action, self.indent_action, self.outdent_action, self.inline_code_action, self.code_fence_action, self.link_action, self.edit_link_action, self.remove_link_action, self.rule_action, self.image_action, self.table_action, self.date_time_action, self.date_action, self.time_action, self.symbol_action):
                action.setEnabled(mutable)
            for action in self.heading_actions: action.setEnabled(mutable)
            self.heading_tabbed_action.setEnabled(mutable)
        self._update_window_title()
