"""Existing x8 command and appearance methods; definitions relocated unchanged."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QKeySequence, QPalette, QTextCharFormat, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QMenu

class EditorPageCommandsAppearanceMixin:

    def _menu_action(
        self, menu, text: str, callback, *, checkable: bool = False,
        shortcut: str | None = None,
    ) -> QAction:
        action = QAction(text, self)
        action.setCheckable(checkable)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def _build_editor_menus(self) -> None:
        self.editor_file_menu = QMenu("File", self)
        file_menu = self.editor_file_menu
        self.save_action = self._menu_action(file_menu, "Save Changes", self.save_to_disk)
        self.discard_action = self._menu_action(file_menu, "Discard Changes", self.confirm_reload)
        file_menu.addSeparator()
        self.properties_action = self._menu_action(file_menu, "Properties…", self.show_properties_dialog)
        file_menu.addSeparator()
        self.external_action = self._menu_action(file_menu, "Open in External Editor", lambda: self.external_editor_requested.emit(self.module))
        self.folder_action = self._menu_action(file_menu, "Open Containing Folder", lambda: self.containing_folder_requested.emit(self.module))
        self.rename_action = self._menu_action(file_menu, "Rename…", lambda: self.rename_requested.emit(self.module))
        self.duplicate_file_action = self._menu_action(file_menu, "Duplicate Markdown File…", lambda: self.duplicate_requested.emit(self.module))
        file_menu.addSeparator()
        self.remove_action = self._menu_action(file_menu, "Remove Markdown File…", lambda: self.remove_requested.emit(self.module))

        self.editor_edit_menu = QMenu("Edit", self)
        edit_menu = self.editor_edit_menu
        self.undo_action = self._menu_action(edit_menu, "Undo", self.editor.undo)
        self.redo_action = self._menu_action(edit_menu, "Redo", self.editor.redo)
        edit_menu.addSeparator()
        self.cut_action = self._menu_action(edit_menu, "Cut", self.editor.cut)
        self.copy_action = self._menu_action(edit_menu, "Copy", self.editor.copy)
        self.paste_plain_action = self._menu_action(edit_menu, "Paste as Plain Text", self.editor.paste_safely)
        self.delete_action = self._menu_action(edit_menu, "Delete", self.editor.delete_selection_or_character)
        edit_menu.addSeparator()
        self.comment_action = self._menu_action(edit_menu, "Toggle Comment", self.editor.toggle_comment)
        self.duplicate_line_action = self._menu_action(edit_menu, "Duplicate Line or Selection", self.editor.duplicate_current_line_or_selection)
        self.select_all_action = self._menu_action(edit_menu, "Select All", self.editor.select_all_text)
        edit_menu.addSeparator()
        self.find_next_action = self._menu_action(edit_menu, "Find Next", self.find_next, shortcut="F3")
        self.find_previous_action = self._menu_action(edit_menu, "Find Previous", self.find_previous, shortcut="Shift+F3")
        # These menu actions belong to EditorPage's private editor menu, which is
        # not itself installed in the Plus MainWindow. Install the actions on the
        # live page as well so their WidgetWithChildren shortcuts actually work.
        self.addAction(self.find_next_action)
        self.addAction(self.find_previous_action)
        self.clear_search_action = self._menu_action(edit_menu, "Clear Search", self.clear_search)
        self.dismiss_find_action = QAction("Close Find/Replace", self)
        self.dismiss_find_action.setShortcut(QKeySequence("Esc"))
        self.dismiss_find_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.dismiss_find_action.triggered.connect(self.hide_find_panel)
        self.addAction(self.dismiss_find_action)
        self.replace_action = self._menu_action(edit_menu, "Replace", self.replace_current)
        self.replace_all_action = self._menu_action(edit_menu, "Replace All", self.replace_all)
        self.goto_action = self._menu_action(edit_menu, "Go to Line…", self.show_go_to_line)

        self.editor_view_menu = QMenu("View", self)
        view_menu = self.editor_view_menu
        self.view_only_action = self._menu_action(view_menu, "Locked Mode", self.toggle_view_only, checkable=True)
        view_menu.addSeparator()
        self.word_wrap_action = self._menu_action(view_menu, "Word Wrap", self.toggle_word_wrap, checkable=True)
        self.line_numbers_action = self._menu_action(view_menu, "Line Numbers", self.toggle_line_numbers, checkable=True)
        self.font_action = self._menu_action(view_menu, "Display Font…", self.choose_display_font)

    def apply_canvas_theme(self) -> None:
        """Apply only Dark Editor canvas presentation while preserving dirty state."""
        self._apply_presentation_safely(self.apply_theme)

    def _canvas_is_light(self) -> bool:
        stored = self.config.get("editor_canvas_light", True)
        return stored if isinstance(stored, bool) else True

    def apply_theme(self) -> None:
        canvas_light = self._canvas_is_light()

        self.editor.set_color_scheme("light" if canvas_light else "dark")
        editor_palette = QPalette(self.editor.palette())
        preview_palette = QPalette(self.preview.palette())
        if canvas_light:
            base_color = QColor("#FFFFFF")
            text_color = QColor("#202124")
            highlight_color = QColor("#0B8781")
            link_color = QColor("#174EA6")
        else:
            base_color = QColor("#151719")
            text_color = QColor("#F1F3F4")
            highlight_color = QColor("#158B86")
            link_color = QColor("#82AAFF")

        for palette in (editor_palette, preview_palette):
            palette.setColor(QPalette.ColorRole.Base, base_color)
            palette.setColor(QPalette.ColorRole.Text, text_color)
            palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        preview_palette.setColor(QPalette.ColorRole.Link, link_color)
        preview_palette.setColor(QPalette.ColorRole.LinkVisited, link_color)

        self.editor.setPalette(editor_palette)
        self.editor.viewport().setPalette(editor_palette)
        self.editor.line_number_area.update()
        self.preview.setPalette(preview_palette)
        self.preview.viewport().setPalette(preview_palette)
        self.preview.document().setDefaultStyleSheet(
            f"a {{ color: {link_color.name()}; }}"
        )
        self._apply_preview_link_color(link_color)

    def _apply_preview_link_color(self, link_color: QColor | None = None) -> None:
        """Keep every rendered anchor on the active canvas's MaqaronyPad blue."""
        if link_color is None:
            canvas_light = self._canvas_is_light()
            link_color = QColor("#174EA6" if canvas_light else "#82AAFF")

        document = self.preview.document()
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        block = document.firstBlock()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid() and fragment.charFormat().isAnchor():
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(
                        fragment.position() + fragment.length(),
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    anchor_format = fragment.charFormat()
                    anchor_format.setForeground(link_color)
                    cursor.setCharFormat(anchor_format)
                iterator += 1
            block = block.next()
        cursor.endEditBlock()

    def _apply_preview_quote_effect(self) -> None:
        """Italicize only Qt-rendered Markdown quotation blocks when requested."""
        if (
            not bool(self.config.get("preview_italic_quotes", False))
            or self.preview_base_font().italic()
        ):
            return

        document = self.preview.document()
        cursor = QTextCursor(document)
        italic = QTextCharFormat()
        italic.setFontItalic(True)
        cursor.beginEditBlock()
        block = document.firstBlock()
        while block.isValid():
            block_format = block.blockFormat()
            if block_format.hasProperty(QTextFormat.Property.BlockQuoteLevel):
                cursor.setPosition(block.position())
                cursor.setPosition(
                    block.position() + max(0, block.length() - 1),
                    QTextCursor.MoveMode.KeepAnchor,
                )
                if cursor.hasSelection():
                    cursor.mergeCharFormat(italic)
            block = block.next()
        cursor.endEditBlock()
