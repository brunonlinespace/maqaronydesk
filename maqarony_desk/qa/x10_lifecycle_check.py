#!/usr/bin/env python3
"""x10 exact original method-copy and inherited lifecycle source safety contract."""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((Path(__file__).parent/'x10-method-fingerprints.json').read_text())
def methods(path,klass):
    text=path.read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
    cs=[x for x in ast.parse(text).body if isinstance(x,ast.ClassDef) and x.name==klass]
    assert len(cs)==1,(path,klass)
    result={}
    for n in cs[0].body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            start=min([n.lineno]+[d.lineno for d in n.decorator_list])-1
            assert n.name not in result
            result[n.name]=hashlib.sha256(''.join(lines[start:n.end_lineno]).encode()).hexdigest()
    return result
host=methods(ROOT/BASE['host'],BASE['host_class'])
life=methods(ROOT/BASE['mixin'],BASE['mixin_class'])
assert life==BASE['moved_sha256'],('lifecycle implementation drift',life)
assert host|life==BASE['all_sha256'],'missing or modified original host methods'
assert not set(host)&set(life),'lifecycle MRO override collision'
assert set(life)==set(BASE['moved_names']),'moved inventory mismatch'

others=[('widgets/editor_page_search_view.py','EditorPageSearchViewMixin'),('widgets/editor_page_printing.py','EditorPagePrintingMixin'),('widgets/editor_page_preferences.py','EditorPagePreferencesMixin'),('widgets/editor_page_commands_appearance.py','EditorPageCommandsAppearanceMixin')]
s=(ROOT/'widgets/editor_page.py').read_text()
assert 'class EditorPage(EditorLifecycleMixin, EditorPageCommandsAppearanceMixin, EditorPagePreferencesMixin, EditorPagePrintingMixin, EditorPageSearchViewMixin, QWidget):' in s
assert 'from mepynamu.widgets.editor_lifecycle import EditorLifecycleMixin' in s

seen=set(host)|set(life)
for name,klass in others:
    group=methods(ROOT/name,klass)
    assert not (seen&set(group)),(name,'inherited method collision')
    seen|=set(group)
assert 'def load_from_disk' in (ROOT/BASE['mixin']).read_text() if BASE['host_class']=='EditorPage' else 'def rename_file' in (ROOT/BASE['mixin']).read_text()
README=(ROOT.parent/'README.md').read_bytes()
assert b'Current release: **1.0.0-x10.0**' in README
prior=ROOT.parent.parent/(('MaqaronyPad-1.0.0-x9.0-source' if BASE['host_class']=='MaqaronyPadWindow' else 'MepyNamu-1.0.0-x8.0-source'))/'README.md'
if prior.is_file():
    original=prior.read_bytes()
    baseline=BASE['baseline'].encode()
    assert README==original.replace(baseline,b'1.0.0-x10.0'), 'GitHub README drift outside version'
print('PASS x10: exact lifecycle definition identity, complete host inventory, no MRO override, approved README version')
