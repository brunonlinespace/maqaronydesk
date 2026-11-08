# Original x5.0 preferences methods relocated unchanged for x6.0.
from __future__ import annotations
from PyQt6.QtGui import QFont, QFontDatabase

class EditorPagePreferencesMixin:

    def apply_preferences(self) -> None:
        """Apply shared MaqaronyPad display preferences without mutating document state."""
        def apply() -> None:
            self.word_wrap_action.setChecked(bool(self.config.get("editor_word_wrap", True)))
            self.line_numbers_action.setChecked(bool(self.config.get("editor_line_numbers", True)))
            self.editor.set_word_wrap_enabled(self.word_wrap_action.isChecked())
            self.editor.set_line_numbers_visible(self.line_numbers_action.isChecked())
            self.editor.set_tab_width_spaces(
                self.config.get_int("editor_tab_width_spaces", 4, minimum=1, maximum=16)
            )
            fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
            family = str(self.config.get("editor_font_family", "") or "").strip() or fixed.family()
            size = self.config.get_int("editor_font_size", 11, minimum=6, maximum=72)
            weight = self.config.get_int("editor_font_weight", 400, minimum=100, maximum=900)
            zoom_percent = self.config.get_int("markopad_zoom", 100, minimum=50, maximum=300)
            font = QFont(family)
            font.setPointSizeF(max(6.0, size * zoom_percent / 100.0))
            font.setStyleHint(QFont.StyleHint.Monospace)
            try:
                font.setWeight(QFont.Weight(weight))
            except (TypeError, ValueError):
                font.setWeight(QFont.Weight.Normal)
            font.setItalic(bool(self.config.get("editor_font_italic", False)))
            self.editor.set_editor_font(font)
            self.apply_preview_font()
            self.editor_status.setVisible(bool(self.config.get("show_status_bar", True)))
            self.apply_theme()
            self.set_view_mode(self.view_mode, persist=False)
        self._apply_presentation_safely(apply)

