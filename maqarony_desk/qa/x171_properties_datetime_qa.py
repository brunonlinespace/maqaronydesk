#!/usr/bin/env python3
"""x17.1: narrow Properties mtime convergence and x17.0 source preservation."""
from __future__ import annotations

import ast
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / 'maqarony_desk'
HERE = PKG / 'qa'
TARGET = PKG / 'widgets/editor_page_printing.py'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preservation() -> None:
    record = json.loads((HERE / 'x171-predecessor-code-sha256.json').read_text())
    assert record['baseline'] == 'MaqaronyDesk 1.0.0-x17.0'
    expected = record['sha256']
    source = TARGET.read_text(encoding='utf-8')
    import_line = 'from datetime import datetime\n'
    old_line = '            modified = str(self.module.modified)'
    new_line = '            modified = datetime.fromtimestamp(stat_result.st_mtime).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")'
    assert source.count(import_line) == source.count(new_line) == 1
    assert old_line not in source
    old_source = source.replace(import_line, '', 1).replace(new_line, old_line, 1)
    assert sha(old_source.encode('utf-8')) == expected['maqarony_desk/widgets/editor_page_printing.py'], 'outside approved Properties change'

    for relative, digest in expected.items():
        if relative == 'maqarony_desk/widgets/editor_page_printing.py':
            continue
        data = (ROOT / relative).read_bytes()
        if relative in {'maqarony_desk/__init__.py', 'maqarony_desk/app_constants.py'}:
            data = data.replace(b'1.0.0-x17.1', b'1.0.0-x17.0')
        assert sha(data) == digest, f'unexpected production or frozen QA change: {relative}'
    assert 'self.setCenterOnScroll(False)' in (PKG / 'widgets/mwpyn/editor_source.py').read_text()
    assert 'if self.view_mode == "preview":' in (PKG / 'widgets/editor_page_search_view.py').read_text()


def run_properties_method() -> None:
    tree = ast.parse(TARGET.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'EditorPagePrintingMixin')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'show_properties_dialog')
    assert len([n for n in cls.body if isinstance(n, ast.FunctionDef)]) == 1

    rows = {}

    class Dialog:
        def __init__(self, parent): self.parent = parent
        def setWindowTitle(self, title): self.title = title
        def setWindowIcon(self, icon): self.icon = icon
        def setMinimumWidth(self, width): self.width = width
        def accept(self): pass
        def exec(self): pass

    class Layout:
        def __init__(self, parent): self.parent = parent
        def setContentsMargins(self, *values): pass
        def setSpacing(self, value): pass
        def addWidget(self, widget): pass

    class Group:
        def __init__(self, title, parent): self.title = title

    class Form:
        FieldGrowthPolicy = SimpleNamespace(AllNonFixedFieldsGrow=1)
        def __init__(self, group): self.group = group
        def setFieldGrowthPolicy(self, policy): pass
        def addRow(self, label, field): rows[(self.group.title, label)] = field.value

    class Field:
        def __init__(self, value, parent): self.value = value
        def setReadOnly(self, value): pass
        def setCursorPosition(self, value): pass

    class ButtonBox:
        StandardButton = SimpleNamespace(Ok=1)
        def __init__(self, kind, parent): self.accepted = SimpleNamespace(connect=lambda fn: None)

    method_cls = ast.ClassDef(name='Page', bases=[], keywords=[], body=[method], decorator_list=[])
    env = {
        'datetime': datetime,
        'QDialog': Dialog,
        'QDialogButtonBox': ButtonBox,
        'QFormLayout': Form,
        'QGroupBox': Group,
        'QLineEdit': Field,
        'QVBoxLayout': Layout,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method_cls], type_ignores=[])), str(TARGET), 'exec'), env)

    class Page(env['Page']):
        def __init__(self, path):
            self.module = SimpleNamespace(path=path, filename=path.name, modified=1.0)
            self.editor = SimpleNamespace(blockCount=lambda: 2, document=lambda: SimpleNamespace(characterCount=lambda: 12), overwriteMode=lambda: False)
            self.file_encoding = 'UTF-8'
            self.file_newline = '\n'
            self.view_only = False
        def windowIcon(self): return None

    with TemporaryDirectory() as directory:
        path = Path(directory) / 'example.md'
        path.write_text('Hello world\n')
        page = Page(path)
        for timestamp in (1609459200, 1730000000):
            os.utime(path, (timestamp, timestamp))
            rows.clear()
            page.show_properties_dialog()
            expected = datetime.fromtimestamp(path.stat().st_mtime).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
            assert rows[('File', 'Modified')] == expected, (rows, expected)
            assert rows[('File', 'Modified')] != str(page.module.modified), 'must not use stale model timestamp'
            assert rows[('File', 'Name')] == 'example.md'
            assert rows[('File', 'Location')] == str(path.parent)
            assert rows[('File', 'Full path')] == str(path)
            assert rows[('File', 'Size')] == '12 bytes'
            assert rows[('File', 'Permissions')].startswith('0o')
            assert rows[('Document', 'Encoding')] == 'UTF-8'
            assert rows[('Document', 'Newline')] == 'LF'
        path.unlink()
        rows.clear()
        page.show_properties_dialog()
        assert all(rows[('File', key)] == 'Unavailable' for key in ('Modified', 'Size', 'Permissions'))
        assert rows[('File', 'Name')] == 'example.md'


def preserved_previous_behavior() -> None:
    spec = importlib.util.spec_from_file_location('frozen_x170_behavior', HERE / 'x170_preview_replace_qa.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    frozen.behavior()
    frozen.preserved_dashboard()


def run() -> None:
    preservation()
    run_properties_method()
    preserved_previous_behavior()
    print('PASS x17.1: Properties uses fresh on-disk mtime in Pad local format; missing-file fallback, x17.0 Preview Replace, Dashboard and source preserved')


if __name__ == '__main__':
    run()
