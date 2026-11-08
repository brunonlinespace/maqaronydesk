#!/usr/bin/env python3
"""1.0.0-x1.0 exact source-identity checks for editor widget extraction."""
import ast,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
expected=json.loads((BASE/'qa/x1-method-fingerprints.json').read_text())
engine=(BASE/'widgets/editor_source.py').read_text()
widgets=(BASE/'widgets/editor_widgets.py').read_text()
def defs(source):
    lines=source.splitlines(keepends=True)
    nodes=ast.parse(source).body
    return {n.name:''.join(lines[min((d.lineno for d in n.decorator_list),default=n.lineno)-1:n.end_lineno]) for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
wd, ed=defs(widgets),defs(engine)
for name in ('HighlightRule','MarkdownHighlighter','LineNumberArea','_scheme'):
    assert name in wd and name not in ed, (name,'definition location')
    assert hashlib.sha256(wd[name].encode()).hexdigest()==expected[name], name
assert 'MarkopadSourceEditor' in ed  # The entire original method inventory is checked by x2_editor_formatting_check.py
for name in ('HighlightRule','MarkdownHighlighter','LineNumberArea','_scheme','MARKDOWN_COLOR_SCHEMES'):
    assert name in engine.split('from ',1)[1], ('missing re-export',name)
assert 'from ' in engine and 'editor_widgets import' in engine
print('PASS: x1.0 original editor widget and source editor definitions preserved')
