#!/usr/bin/env python3
"""x4 source-preservation release gate: all original editor and host methods,
source-view and Find/Replace extraction, renamed source and preview bytes.
"""
from __future__ import annotations
import ast, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
WIDGETS=ROOT/'widgets'
DATA=json.loads((ROOT/'qa/x4-method-fingerprints.json').read_text(encoding="utf-8"))
X3=json.loads((ROOT/'qa/x3-method-fingerprints.json').read_text(encoding="utf-8"))
def methods(path, name):
    source=path.read_text(encoding="utf-8")
    lines=source.splitlines(keepends=True)
    classes=[x for x in ast.parse(source).body if isinstance(x,ast.ClassDef) and x.name==name]
    assert len(classes)==1, (path,name)
    result={}
    for n in classes[0].body:
        if isinstance(n, (ast.FunctionDef,ast.AsyncFunctionDef)):
            begin=min((d.lineno for d in n.decorator_list),default=n.lineno)
            assert n.name not in result,(path,n.name)
            result[n.name]=hashlib.sha256("".join(lines[begin-1:n.end_lineno]).encode()).hexdigest()
    return result
src=WIDGETS/'editor_source.py'
view=WIDGETS/'editor_search_view.py'
fmt=WIDGETS/'editor_formatting.py'
ins=WIDGETS/'editor_insertion.py'
source_m=methods(src,'MarkopadSourceEditor')
view_m=methods(view,'EditorSearchViewMixin')
fmt_m=methods(fmt,'EditorFormattingMixin')
ins_m=methods(ins,'EditorInsertionMixin')
groups=[source_m,view_m,fmt_m,ins_m]
assert all(not (set(left) & set(right)) for i,left in enumerate(groups) for right in groups[i+1:]), 'duplicate inherited method'
assert set(view_m)==set(DATA['moved_source_methods']), 'x4 source extraction inventory drift'
assert set(source_m)|set(view_m)==set(DATA['source_editor_methods']), 'x4 source editor inventory drift'
assert source_m|view_m==DATA['source_editor_methods'], 'x4 source editor original definition modified'
assert {k:v for group in groups for k,v in group.items()}==X3['all_method_sha256'], 'x3 original method inventory changed'
original_class='class MarkopadSourceEditor(EditorSearchViewMixin, EditorInsertionMixin, EditorFormattingMixin, QPlainTextEdit):'
assert original_class in src.read_text(), 'canonical class inheritance drift'
assert 'EditorSearchViewMixin' in src.read_text() and 'EditorSearchViewMixin' in view.read_text()
HOST=ROOT/'widgets/editor_page.py'
host_m=methods(HOST,'EditorPage')
host_m.update(methods(ROOT/'widgets/editor_lifecycle.py','EditorLifecycleMixin'))
host_view=methods(ROOT/'widgets/editor_page_search_view.py','EditorPageSearchViewMixin')
host_printing=methods(ROOT/'widgets/editor_page_printing.py','EditorPagePrintingMixin')
host_preferences=methods(ROOT/'widgets/editor_page_preferences.py','EditorPagePreferencesMixin')
host_commands=methods(ROOT/'widgets/editor_page_commands_appearance.py','EditorPageCommandsAppearanceMixin')
assert set(host_printing)=={'show_properties_dialog'}
assert not (set(host_m)&set(host_view)) and not ((set(host_m)|set(host_view))&set(host_printing)) and not ((set(host_m)|set(host_view)|set(host_printing))&set(host_preferences)), 'window/editor-page method override collision'
assert set(host_view)==set(DATA['moved_host_methods']), 'x4 host extraction inventory drift'
assert host_m|host_view|host_printing|host_preferences|host_commands==DATA['host_methods'], 'original host implementation changed'
preview=WIDGETS/'editor_preview.py'
assert hashlib.sha256(preview.read_bytes()).hexdigest()==DATA['unchanged_preview_sha256'], 'preview content changed'
# x5 completes approved x4 filename convergence: obsolete compatibility aliases are absent.
assert not (WIDGETS/'markopad_source_editor.py').exists(), 'obsolete filename returned: markopad_source_editor.py'
assert not (WIDGETS/'markopad_preview.py').exists(), 'obsolete filename returned: markopad_preview.py'
print(f"PASS x4: {len(source_m)+len(view_m)+len(fmt_m)+len(ins_m)} unchanged source methods; {len(host_m)+len(host_view)} unchanged host methods; {len(view_m)} + {len(host_view)} relocated; preview bytes exact")
