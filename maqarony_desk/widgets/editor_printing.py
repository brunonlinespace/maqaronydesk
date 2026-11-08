# Existing x4 method bodies relocated unchanged for the x5 printing/document-information stage.
from __future__ import annotations
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog


class EditorPrintingMixin:

    def _printable_document(self):
        page = self._current_page()
        if page is None: return None
        doc = QTextDocument(self); doc.setDefaultFont(QApplication.font())
        doc.setBaseUrl(QUrl.fromLocalFile(str(page.module.path.parent) + "/"))
        try: doc.setMarkdown(page.editor.toPlainText())
        except AttributeError: doc.setPlainText(page.editor.toPlainText())
        return doc

    def _print_current(self) -> None:
        from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
        doc = self._printable_document()
        if doc is None: return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution); dialog = QPrintDialog(printer, self); dialog.setWindowTitle("Print — MaqaronyDesk")
        if dialog.exec() == QDialog.DialogCode.Accepted: doc.print(printer)

    def _export_pdf_current(self) -> None:
        from PyQt6.QtPrintSupport import QPrinter
        page = self._current_page(); doc = self._printable_document()
        if page is None or doc is None: return
        initial = str(page.module.path.with_suffix(".pdf")); path, _ = QFileDialog.getSaveFileName(self, "Export PDF — MaqaronyDesk", initial, "PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        destination = Path(path)
        try:
            previous_stat = destination.stat()
            previous_fingerprint = (previous_stat.st_ino, previous_stat.st_size, previous_stat.st_mtime_ns)
        except OSError:
            previous_fingerprint = None
        printer = QPrinter(QPrinter.PrinterMode.HighResolution); printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat); printer.setOutputFileName(path); doc.print(printer)
        try:
            current_stat = destination.stat()
            fingerprint = (current_stat.st_ino, current_stat.st_size, current_stat.st_mtime_ns)
            if current_stat.st_size > 0 and fingerprint != previous_fingerprint:
                with destination.open("rb") as output:
                    is_pdf = output.read(5) == b"%PDF-"
                if is_pdf:
                    page.show_editor_status(f"Exported PDF to {path}", 4000)
        except OSError:
            pass

