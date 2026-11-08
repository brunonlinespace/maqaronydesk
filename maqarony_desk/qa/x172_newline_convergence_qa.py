#!/usr/bin/env python3
"""x17.2: exact MaqaronyPad newline-policy parity; preserve x17.1 code and QA."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / 'maqarony_desk'
HERE = PKG / 'qa'
TARGET = PKG / 'widgets/editor_lifecycle.py'
OLD = '        crlf = content.count("\\r\\n")\n        lf = content.count("\\n") - crlf\n        cr = content.count("\\r") - crlf\n        count, newline = max(((crlf, "\\r\\n"), (lf, "\\n"), (cr, "\\r")))\n        return newline if count else "\\n"'
NEW = '        crlf = content.count("\\r\\n")\n        stripped = content.replace("\\r\\n", "")\n        cr = stripped.count("\\r")\n        lf = stripped.count("\\n")\n        if crlf >= cr and crlf >= lf and crlf:\n            return "\\r\\n"\n        if cr > lf and cr:\n            return "\\r"\n        return "\\n"'

# Frozen from MaqaronyPad 1.0.0-x13.0, document_io.py:_detect_newline.
# The parameter alone is renamed text -> content to retain Desk's public method.
PAD_AUTHORITY = '        crlf = content.count("\\r\\n")\n        stripped = content.replace("\\r\\n", "")\n        cr = stripped.count("\\r")\n        lf = stripped.count("\\n")\n        if crlf >= cr and crlf >= lf and crlf:\n            return "\\r\\n"\n        if cr > lf and cr:\n            return "\\r"\n        return "\\n"'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preserve_old_code() -> None:
    record = json.loads((HERE / 'x172-predecessor-code-sha256.json').read_text())
    assert record['baseline'] == 'MaqaronyDesk 1.0.0-x17.1'
    expected = record['sha256']
    actual_source = TARGET.read_text(encoding='utf-8')
    assert actual_source.count(OLD) == 0
    assert actual_source.count(NEW) == 1
    assert NEW == PAD_AUTHORITY
    prior_source = actual_source.replace(NEW, OLD, 1)
    assert sha(prior_source.encode('utf-8')) == expected['maqarony_desk/widgets/editor_lifecycle.py']
    for relative, checksum in expected.items():
        if relative == 'maqarony_desk/widgets/editor_lifecycle.py':
            continue
        data = (ROOT / relative).read_bytes()
        if relative in {'maqarony_desk/__init__.py', 'maqarony_desk/app_constants.py'}:
            data = data.replace(b'1.0.0-x17.2', b'1.0.0-x17.1')
        assert sha(data) == checksum, f'unexpected production/historical QA edit: {relative}'
    assert 'self.setCenterOnScroll(False)' in (PKG / 'widgets/mwpyn/editor_source.py').read_text()
    assert 'if self.view_mode == "preview":' in (PKG / 'widgets/editor_page_search_view.py').read_text()


def assert_pad_method_and_cases() -> None:
    tree = ast.parse(TARGET.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'EditorLifecycleMixin')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_detect_newline_style')
    expected_lines = 'def _detect_newline_style(content: str) -> str:\n' + NEW + '\n'
    expected_ast = ast.parse(expected_lines).body[0]
    assert ast.dump(method.args, include_attributes=False) == ast.dump(expected_ast.args, include_attributes=False), 'signature differs from Pad adapter'
    assert [ast.dump(node, include_attributes=False) for node in method.body] == [ast.dump(node, include_attributes=False) for node in expected_ast.body], 'not Pad-authoritative logic'
    assert len(method.decorator_list) == 1 and isinstance(method.decorator_list[0], ast.Name) and method.decorator_list[0].id == 'staticmethod'
    env = {}
    isolated = ast.Module(body=[ast.FunctionDef(name='detect',args=method.args,body=method.body,decorator_list=[],returns=method.returns,type_comment=None)],type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), '<isolated-newline-method>', 'exec'),env)
    detect = env['detect']

    def pad_contract(content: str) -> str:
        crlf = content.count('\r\n')
        stripped = content.replace('\r\n', '')
        cr = stripped.count('\r')
        lf = stripped.count('\n')
        if crlf >= cr and crlf >= lf and crlf:
            return '\r\n'
        if cr > lf and cr:
            return '\r'
        return '\n'

    assert detect('') == detect('abc') == '\n'
    assert detect('a\r\nb') == '\r\n'
    assert detect('a\rb') == '\r'
    assert detect('a\nb') == '\n'
    assert detect('a\rb\nc') == '\n'   # CR vs LF exact tie
    assert detect('a\r\nb\rc') == '\r\n'  # CRLF vs CR exact tie
    assert detect('a\r\nb\nc') == '\r\n'  # CRLF vs LF exact tie
    assert detect('a\r\nb\rc\nd') == '\r\n'  # three-way tie
    assert detect('a\rb\rc\nd') == '\r'   # CR majority
    assert detect('a\nb\nc\rd') == '\n'   # LF majority
    for counts in itertools.product(range(6), repeat=3):
        crlf, cr, lf = counts
        for ordering in (('\r\n', '\r', '\n'), ('\n', '\r\n', '\r')):
            sample = 'test' + ''.join(end * {'\r\n':crlf, '\r':cr, '\n':lf}[end] for end in ordering)
            assert detect(sample) == pad_contract(sample), (counts,ordering)
    # No changes to the existing load/save/encoding method body are allowed.
    for fragment in ('self._decode_source(data)', 'newline = self._detect_newline_style(text)',
                     r'normalised = portable_text.replace("\r\n", "\n").replace("\r", "\n")',
                     'self.file_newline = newline', 'self.file_bom = bom',
                     r'content = content.replace("\n", self.file_newline)'):
        assert fragment in TARGET.read_text(encoding='utf-8'),fragment


def previous_release_regressions() -> None:
    spec = importlib.util.spec_from_file_location('frozen_x171_behavior',HERE/'x171_properties_datetime_qa.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.run_properties_method()
    old.preserved_previous_behavior()


def run() -> None:
    preserve_old_code()
    assert_pad_method_and_cases()
    previous_release_regressions()
    print('PASS x17.2: Pad-authoritative newline majority/ties; x17.1 Properties, x17.0 Preview Only, prior production and QA preserved')


if __name__ == '__main__':
    run()
