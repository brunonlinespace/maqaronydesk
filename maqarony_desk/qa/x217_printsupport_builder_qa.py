#!/usr/bin/env python3
"""x21.7: ensure the AppImage PrintSupport preflight inspects the real mixin."""
from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
builder = (root / 'packaging/fedora/build-appimage.sh').read_text()
main_source = (root / 'widgets/main_window.py').read_text()
print_source = (root / 'widgets/editor_printing.py').read_text()

assert 'EDITOR_PRINTING="$PROGRAM_ROOT/widgets/editor_printing.py"' in builder
assert '"$MAIN_WINDOW" "$EDITOR_PRINTING"' in builder
assert '\'from PyQt6.QtPrintSupport import QPrintDialog, QPrinter\' "$EDITOR_PRINTING"' in builder
assert '\'QPrinter.OutputFormat.PdfFormat\' "$EDITOR_PRINTING"' in builder
assert '\'from maqarony_desk.widgets.editor_printing import EditorPrintingMixin\' "$MAIN_WINDOW"' in builder
assert '\'EditorPrintingMixin, QMainWindow\' "$MAIN_WINDOW"' in builder
assert '\'from PyQt6.QtPrintSupport import QPrintDialog, QPrinter\' "$MAIN_WINDOW"' not in builder
assert '\'QPrinter.OutputFormat.PdfFormat\' "$MAIN_WINDOW"' not in builder
assert 'Qt PrintSupport was not bundled' in builder
assert "-name '*Qt6PrintSupport*' -o -name '*QtPrintSupport*'" in builder

main = ast.parse(main_source)
printing = ast.parse(print_source)
assert any(isinstance(n, ast.ImportFrom) and n.module == 'maqarony_desk.widgets.editor_printing'
           and any(a.name == 'EditorPrintingMixin' for a in n.names) for n in main.body)
assert any(isinstance(n, ast.ClassDef) and n.name == 'MainWindow'
           and any(isinstance(b, ast.Name) and b.id == 'EditorPrintingMixin' for b in n.bases)
           for n in main.body)
cls = next(n for n in printing.body if isinstance(n, ast.ClassDef) and n.name == 'EditorPrintingMixin')
methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
assert {'_print_current', '_export_pdf_current', '_printable_document'} <= methods.keys()
assert any(isinstance(n, ast.ImportFrom) and n.module == 'PyQt6.QtPrintSupport'
           and {a.name for a in n.names} >= {'QPrintDialog', 'QPrinter'}
           for n in ast.walk(methods['_print_current']))
assert any(isinstance(n, ast.ImportFrom) and n.module == 'PyQt6.QtPrintSupport'
           and 'QPrinter' in {a.name for a in n.names} for n in ast.walk(methods['_export_pdf_current']))
assert any(isinstance(n, ast.Attribute) and ast.unparse(n) == 'QPrinter.OutputFormat.PdfFormat'
           for n in ast.walk(methods['_export_pdf_current']))
print('PASS x21.7 PrintSupport preflight follows EditorPrintingMixin; frozen Qt bundle validation retained')
