#!/usr/bin/env python3
"""Qt-free exercise of the x18.2 Markdown-open path and exact production scope."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Support the current release gate, which invokes QA by file path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from maqarony_desk.services.file_io import (
    FileStateChangedError,
    FileTooLargeError,
    UnsupportedFileError,
    read_regular_file,
)

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / 'widgets/editor_lifecycle.py'
PAGE = ROOT / 'widgets/editor_page.py'

# Confirm no other production Python methods changed from the preceding release.
reference = json.loads((ROOT / 'qa/x182-predecessor-python-sha256.json').read_text())
assert reference['baseline'] == '1.0.0-x18.1'
for relative, expected in reference['unchanged_production_python_sha256'].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert actual == expected, f'Unapproved production change: {relative}'

source = LIFECYCLE.read_text()
assert 'encoding_status_label' not in source, 'Retired status label accessed in lifecycle'
assert source.count('        self._update_cursor_position()\n') >= 1
lifecycle = ast.parse(source)
klass = next(node for node in lifecycle.body if isinstance(node, ast.ClassDef) and node.name == 'EditorLifecycleMixin')
load = next(node for node in klass.body if isinstance(node, ast.FunctionDef) and node.name == 'load_from_disk')
# The only x18.1->x18.2 code change is deletion of the obsolete label update.
expected_lifecycle_digest = '778fcac3a38b9acafa032fb793ea4c3b217b293b5e192305f8fbd34fa14664ea'
assert hashlib.sha256(source.encode()).hexdigest() == expected_lifecycle_digest, 'Lifecycle changed beyond approved line deletion'

page_tree = ast.parse(PAGE.read_text())
page_cls = next(node for node in page_tree.body if isinstance(node, ast.ClassDef) and node.name == 'EditorPage')
update = next(node for node in page_cls.body if isinstance(node, ast.FunctionDef) and node.name == '_update_cursor_position')

class FakeCursor:
    def clearSelection(self): pass
    def movePosition(self, position): assert position == 'Start'
    def blockNumber(self): return 0
    def positionInBlock(self): return 0

class FakeScrollbar:
    def minimum(self): return 0
    def setValue(self, value): assert value == 0

class FakeDocument:
    def clearUndoRedoStacks(self): pass

class FakeEditor:
    MAX_DOCUMENT_CHARACTERS = 10_000
    def __init__(self): self.text = ''
    def load_text(self, text): self.text = text
    def textCursor(self): return FakeCursor()
    def setTextCursor(self, cursor): pass
    def ensureCursorVisible(self): pass
    def verticalScrollBar(self): return FakeScrollbar()
    def document(self): return FakeDocument()
    def mark_clean(self): pass
    def toPlainText(self): return self.text
    def blockCount(self): return self.text.count('\n') + 1
    def overwriteMode(self): return False

class FakeLabel:
    def setText(self, value): self.text = value
    def setToolTip(self, value): self.tooltip = value

class FakeMessage:
    def __init__(self): self.messages = []
    def emit(self, value): self.messages.append(value)

class FakeRepository:
    def __init__(self): self.operations = []
    def set_dirty(self, path, dirty): self.operations.append((path, dirty))

class FakePreview:
    def set_document_path(self, path): self.path = path

class FakeConfig:
    def get_int(self, *args, **kwargs): return 100

# Evaluate the real load/update method bodies, not a mock reimplementation.
class FakeQTextCursor:
    class MoveOperation:
        Start = 'Start'

namespace = {
    'read_regular_file': read_regular_file,
    'FileStateChangedError': FileStateChangedError,
    'FileTooLargeError': FileTooLargeError,
    'UnsupportedFileError': UnsupportedFileError,
    'QTextCursor': FakeQTextCursor,
    'strip_legacy_envelope': lambda text: (text, False),
    'QMessageBox': SimpleNamespace(information=lambda *a: None, warning=lambda *a: None, critical=lambda *a: None),
    'OSError': OSError,
    'MemoryError': MemoryError,
}
for method in (load, update):
    definition = ast.Module(body=[method], type_ignores=[])
    exec(compile(ast.fix_missing_locations(definition), '<real-editor-method>', 'exec'), namespace)

class FakeEditorPage:
    MAX_FILE_BYTES = 1024 * 1024
    _ignore_document_signal = False
    view_mode = 'split'
    def __init__(self, path):
        self.module = SimpleNamespace(path=path, filename=path.name, loaded=False, modified=None, size=0)
        self.editor = FakeEditor()
        self.repository = FakeRepository()
        self.preview = FakePreview()
        self.config = FakeConfig()
        self.status_indicators_label = FakeLabel()
        self.status_message = FakeMessage()
        self.file_encoding = 'utf-8'
        self.file_newline = '\n'
        self.refreshed = False
        self.scheduled = False
        # Deliberately no encoding_status_label attribute: x18.1 crashes here.
    def _decode_source(self, data): return data.decode('utf-8'), 'utf-8', b''
    def _looks_binary_text(self, text): return False
    def _detect_newline_style(self, text): return '\r\n' if '\r\n' in text else '\n'
    def _set_backing_state(self, state): self.backing_state = state
    def _refresh_header(self): pass
    def refresh_search(self): self.refreshed = True
    def schedule_preview(self): self.scheduled = True
    _update_cursor_position = namespace['_update_cursor_position']
    load_from_disk = namespace['load_from_disk']

with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary) / 'Example.md'
    path.write_bytes(b'Hello\r\nWorld\r\n')
    owner = FakeEditorPage(path)
    assert owner.load_from_disk(show_errors=False) is True
    assert owner.module.loaded is True
    assert owner.editor.text == 'Hello\nWorld\n'
    assert owner.file_encoding == 'utf-8' and owner.file_newline == '\r\n'
    assert owner.status_indicators_label.text == 'Insert · Ln 1/3 Col 1 Chars 12 · UTF-8 CRLF · Split 100%'
    assert owner.status_indicators_label.tooltip == owner.status_indicators_label.text
    assert owner.repository.operations == [(path, False)]
    assert owner.backing_state == 'normal' and owner.refreshed and owner.scheduled
    assert owner.preview.path == str(path)
    assert owner.status_message.messages == ['Loaded Example.md']

print('PASS x18.2 successful document load, consolidated encoding/newline indicators and predecessor preservation')
