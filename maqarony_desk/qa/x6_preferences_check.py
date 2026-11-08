#!/usr/bin/env python3
"""x6 strict method-copy parity, architecture and GitHub root README content gate."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT.name
BASE=ROOT.parent
QA=Path(__file__).parent
FROZEN=json.loads((QA/'x6-method-fingerprints.json').read_text())

def methods(file, name):
    s=file.read_text(encoding='utf-8'); lines=s.splitlines(keepends=True)
    cs=[x for x in ast.parse(s).body if isinstance(x,ast.ClassDef) and x.name==name]
    assert len(cs)==1,(file,name)
    out={}
    for n in cs[0].body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            start=min([n.lineno,*[d.lineno for d in n.decorator_list]])-1
            assert n.name not in out
            out[n.name]=hashlib.sha256(''.join(lines[start:n.end_lineno]).encode()).hexdigest()
    return out

host=methods(BASE/FROZEN['source'],FROZEN['host_class'])
if FROZEN['host_class']=='EditorPage':host.update(methods(ROOT/'widgets/editor_lifecycle.py','EditorLifecycleMixin'))
mixin=methods(BASE/FROZEN['mixin'],FROZEN['mixin_class'])
assert mixin==FROZEN['method_sha256'], 'extracted preference method source differs from x5'
assert not set(host)&set(mixin), 'a preference method has multiple implementations'
commands=methods(ROOT/'widgets/editor_page_commands_appearance.py','EditorPageCommandsAppearanceMixin')
assert host|mixin|commands==FROZEN['x5_host_methods'], 'original editor host method missing or changed'
readme=(BASE/'README.md').read_bytes()
assert hashlib.sha256(readme.replace(b'1.0.0-x10.0', b'1.0.0-x6.1')).hexdigest()==FROZEN['github_readme_sha256'], 'unapproved alteration in GitHub root README'
assert b'Current release: **1.0.0-x10.0**' in readme
if PKG=='maqarony_pad':
    main=(ROOT/'maqarony_pad.py').read_text()
    assert 'class MaqaronyPadWindow(EditorPreferencesMixin, EditorPrintingMixin, WindowSearchViewMixin, QMainWindow):' in main
    assert '_editor_preferences.save_json_settings = save_json_settings' in main
    assert 'from editor_preferences import EditorPreferencesMixin' in main
    assert '"$PROGRAM_ROOT/editor_preferences.py"' in (ROOT/'packaging/fedora/build-appimage.sh').read_text()
else:
    main=(ROOT/'widgets/editor_page.py').read_text()
    assert 'class EditorPage(EditorLifecycleMixin, EditorPageCommandsAppearanceMixin, EditorPagePreferencesMixin, EditorPagePrintingMixin, EditorPageSearchViewMixin, QWidget):' in main
    assert 'from mepynamu.widgets.editor_page_preferences import EditorPagePreferencesMixin' in main
print('PASS x6: original preference implementations exact; README restored/locked; mixin bindings verified')
