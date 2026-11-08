# Existing x4 method bodies relocated unchanged for the x5 printing/document-information stage.
from __future__ import annotations
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLineEdit, QVBoxLayout


class EditorPagePrintingMixin:

    def show_properties_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Properties — MaqaronyDesk")
        dialog.setWindowIcon(self.windowIcon())
        dialog.setMinimumWidth(640)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(12)

        def add_group(title: str, rows) -> None:
            box = QGroupBox(title, dialog)
            form = QFormLayout(box)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for label, value in rows:
                field = QLineEdit(str(value), box)
                field.setReadOnly(True)
                field.setCursorPosition(0)
                form.addRow(label, field)
            layout.addWidget(box)

        try:
            stat_result = self.module.path.stat()
            permissions = oct(stat_result.st_mode & 0o777)
            modified = datetime.fromtimestamp(stat_result.st_mtime).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            size = f"{stat_result.st_size:,} bytes"
        except OSError:
            permissions = modified = size = "Unavailable"

        add_group("File", (
            ("Name", self.module.filename),
            ("Location", str(self.module.path.parent)),
            ("Full path", str(self.module.path)),
            ("Size", size),
            ("Modified", modified),
            ("Permissions", permissions),
        ))
        add_group("Document", (
            ("Lines", f"{self.editor.blockCount():,}"),
            ("Characters", f"{max(0, self.editor.document().characterCount() - 1):,}"),
            ("Encoding", self.file_encoding),
            ("Newline", {"\n": "LF", "\r\n": "CRLF", "\r": "CR"}.get(self.file_newline, "LF")),
            ("Locked Mode", "On" if self.view_only else "Off"),
            ("Edit mode", "Overwrite" if self.editor.overwriteMode() else "Insert"),
        ))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, dialog)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

