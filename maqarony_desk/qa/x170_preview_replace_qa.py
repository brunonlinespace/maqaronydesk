#!/usr/bin/env python3
"""x17.0: Qt-free Preview Only Replace protection and x16.2 code preservation."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "maqarony_desk"
HERE = PKG / "qa"
TARGET = PKG / "widgets/editor_page_search_view.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preservation() -> None:
    baseline = json.loads((HERE / "x170-predecessor-code-sha256.json").read_text())
    assert baseline["baseline"] == "MaqaronyDesk 1.0.0-x16.2"
    expected = baseline["sha256"]
    old_single = '''        if self.view_only:
            self.show_view_only_edit_prompt()
            return False
        query = self.find_input.text()'''
    new_single = '''        if self.view_only:
            self.show_view_only_edit_prompt()
            return False
        if self.view_mode == "preview":
            return False
        query = self.find_input.text()'''
    old_all = old_single.replace("return False", "return 0")
    new_all = new_single.replace("return False", "return 0")
    source = TARGET.read_text()
    assert source.count(new_single) == source.count(new_all) == 1
    assert sha(source.replace(new_single, old_single).replace(new_all, old_all).encode()) == expected['maqarony_desk/widgets/editor_page_search_view.py'], "non-scope source change"
    for relative, expected_hash in expected.items():
        if relative == 'maqarony_desk/widgets/editor_page_search_view.py':
            continue
        data = (ROOT / relative).read_bytes()
        if relative in {'maqarony_desk/__init__.py', 'maqarony_desk/app_constants.py'}:
            data = data.replace(b'1.0.0-x17.0', b'1.0.0-x16.2')
        assert sha(data) == expected_hash, relative
    assert 'self.setCenterOnScroll(False)' in (PKG / 'widgets/mwpyn/editor_source.py').read_text()

    # Earlier Dashboard and end-of-file scrolling test files are kept as frozen history.
    assert 'maqarony_desk/qa/x162_source_scrolling_qa.py' in expected
    assert 'maqarony_desk/qa/x160_dashboard_actions_qa.py' in expected


def method_functions():
    tree = ast.parse(TARGET.read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "EditorPageSearchViewMixin")
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in ('replace_current', 'replace_all')]
    assert len(methods) == 2
    for method in methods:
        assert len(method.body) >= 3
        locked, preview = method.body[:2]
        assert isinstance(locked, ast.If) and ast.unparse(locked.test) == 'self.view_only'
        assert isinstance(preview, ast.If) and ast.unparse(preview.test) == "self.view_mode == 'preview'"
        assert len(preview.body) == 1 and isinstance(preview.body[0], ast.Return)
        assert isinstance(preview.body[0].value, ast.Constant)
        assert preview.body[0].value.value == (False if method.name == 'replace_current' else 0)
    return methods


class Cursor:
    def __init__(self, doc_or_cursor):
        if isinstance(doc_or_cursor, Cursor):
            self.doc, self.position = doc_or_cursor.doc, doc_or_cursor.position
            self.start, self.end = doc_or_cursor.start, doc_or_cursor.end
            self.null = doc_or_cursor.null
        else:
            self.doc = doc_or_cursor
            self.position = 0
            self.start = self.end = None
            self.null = False

    def isNull(self): return self.null
    def hasSelection(self): return self.start is not None and self.start != self.end
    def selectionStart(self): return self.start
    def selectionEnd(self): return self.end
    def setPosition(self, value):
        self.position = value
        self.start = self.end = None
    def insertText(self, text):
        assert self.hasSelection()
        self.doc.value = self.doc.value[:self.start] + text + self.doc.value[self.end:]
        self.position = self.start + len(text)
        self.start = self.end = None
    def beginEditBlock(self): self.doc.edit_blocks += 1
    def endEditBlock(self): self.doc.edit_blocks -= 1


class Document:
    def __init__(self, value):
        self.value = value
        self.edit_blocks = 0
    def characterCount(self): return len(self.value) + 1
    def find(self, query, cursor, flags):
        index = self.value.find(query, cursor.position)
        result = Cursor(self)
        if index < 0:
            result.null = True
            return result
        result.start = index
        result.end = result.position = index + len(query)
        return result


class Field:
    def __init__(self, value): self.value = value; self.focused = False
    def text(self): return self.value
    def setFocus(self): self.focused = True


class Signal:
    def __init__(self): self.messages = []
    def emit(self, message): self.messages.append(message)


class FakeEditor:
    MAX_DOCUMENT_CHARACTERS = 10000
    def __init__(self, document):
        self._document = document
        self._cursor = Cursor(document)
        self._cursor.start = 0
        self._cursor.end = self._cursor.position = 3
    def document(self): return self._document
    def textCursor(self): return self._cursor
    def setTextCursor(self, cursor): self._cursor = cursor


def behavior():
    methods = method_functions()
    module = ast.Module(body=[ast.ClassDef(name='Probe', bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[])
    env = {'QTextCursor': Cursor}
    exec(compile(ast.fix_missing_locations(module), str(TARGET), 'exec'), env)
    cls = env['Probe']

    def editor(mode, locked=False):
        page = cls()
        page.view_mode, page.view_only = mode, locked
        page.find_input, page.replace_input = Field('old'), Field('NEW')
        page.editor = FakeEditor(Document('old old'))
        page.MAX_SEARCH_QUERY_CHARACTERS = 10000
        page.MAX_SEARCH_MATCHES = 10000
        page._replace_flags = lambda: None
        page._selection_matches_replace_query = lambda cursor, query: cursor.hasSelection() and cursor.doc.value[cursor.start:cursor.end] == query
        page.find_next = lambda: False
        page.refresh_search = lambda: None
        page.status_message = Signal()
        page.prompt_count = 0
        page.show_view_only_edit_prompt = lambda: setattr(page, 'prompt_count', page.prompt_count + 1)
        page._search_refresh_suspended = False
        return page

    for mode in ('preview', 'source', 'split'):
        for operation in ('replace_current', 'replace_all'):
            page = editor(mode)
            before = page.editor.document().value
            result = getattr(page, operation)()
            if mode == 'preview':
                assert result in (False, 0) and page.editor.document().value == before
                assert page.prompt_count == 0, 'Preview Only must not trigger Locked Mode warning'
            elif operation == 'replace_current':
                assert result is True and page.editor.document().value == 'NEW old', (mode, operation)
            else:
                assert result == 2 and page.editor.document().value == 'NEW NEW', (mode, operation)
                assert page.editor.document().edit_blocks == 0
    for operation in ('replace_current', 'replace_all'):
        page = editor('preview', locked=True)
        before = page.editor.document().value
        assert getattr(page, operation)() in (False, 0)
        assert page.prompt_count == 1 and page.editor.document().value == before


def preserved_dashboard():
    spec = importlib.util.spec_from_file_location('frozen_x160_dashboard', HERE / 'x160_dashboard_actions_qa.py')
    historical = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(historical)
    historical.dashboard_buttons()
    historical.editor_routes()
    historical.predecessor_behaviour()


def run():
    preservation()
    behavior()
    preserved_dashboard()
    print('PASS x17.0: Preview Only replacement blocked; Source/Split replacement works; Locked Mode and x16.2 source preserved; Dashboard checks pass')


if __name__ == '__main__':
    run()
