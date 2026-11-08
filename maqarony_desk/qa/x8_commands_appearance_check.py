#!/usr/bin/env python3
"""x8 strict source identity, inheritance and README content gate."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FROZEN=json.loads((ROOT/'qa/x8-method-fingerprints.json').read_text())
def methods(path,classname):
    s=path.read_text(); lines=s.splitlines(keepends=True)
    classes=[n for n in ast.parse(s).body if isinstance(n,ast.ClassDef) and n.name==classname]
    assert len(classes)==1,(path,classname)
    out={}
    for n in classes[0].body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            start=min([n.lineno]+[d.lineno for d in n.decorator_list])-1
            assert n.name not in out
            out[n.name]=hashlib.sha256(''.join(lines[start:n.end_lineno]).encode()).hexdigest()
    return out

for category in ('main','page'):
    entry=FROZEN[category]
    prefix=ROOT/'widgets'
    hostfile=prefix/('main_window.py' if category=='main' else 'editor_page.py')
    hostclass='MainWindow' if category=='main' else 'EditorPage'
    mixfile=prefix/('editor_commands_appearance.py' if category=='main' else 'editor_page_commands_appearance.py')
    mixclass='EditorCommandsAppearanceMixin' if category=='main' else 'EditorPageCommandsAppearanceMixin'
    host=methods(hostfile,hostclass)
    if category=='page':host.update(methods(ROOT/'widgets/editor_lifecycle.py','EditorLifecycleMixin'))
    moved=methods(mixfile,mixclass)
    assert moved==entry['relocated'], (category,'relocated methods changed')
    assert not (set(host)&set(moved)), (category,'duplicate method')
    assert host|moved==entry['fingerprints'], (category,'baseline method lost or changed')
    others=[('editor_printing.py','EditorPrintingMixin')] if category=='main' else [('editor_page_search_view.py','EditorPageSearchViewMixin'),('editor_page_printing.py','EditorPagePrintingMixin'),('editor_page_preferences.py','EditorPagePreferencesMixin')]
    all_groups=[host,moved]+[methods(prefix/f,k) for f,k in others]
    assert all(not (set(a)&set(b)) for i,a in enumerate(all_groups) for b in all_groups[i+1:]), (category,'duplicate inherited method')
assert 'class MainWindow(EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):' in (ROOT/'widgets/main_window.py').read_text()
assert 'class EditorPage(EditorLifecycleMixin, EditorPageCommandsAppearanceMixin, EditorPagePreferencesMixin, EditorPagePrintingMixin, EditorPageSearchViewMixin, QWidget):' in (ROOT/'widgets/editor_page.py').read_text()
README=(ROOT.parent/'README.md').read_bytes()
F6=json.loads((ROOT/'qa/x6-method-fingerprints.json').read_text())
assert hashlib.sha256(README.replace(b'1.0.0-x10.0',b'1.0.0-x6.1')).hexdigest()==F6['github_readme_sha256'], 'GitHub root README changed beyond version'
print('PASS x8: MepyNamu command/menu and editor appearance definitions exact; no inherited method collisions; root README locked')
