#!/usr/bin/env python3
"""x5 release gate: frozen x4 definitions, printing/Properties extraction, filename convergence."""
from __future__ import annotations
import ast,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
FROZEN=json.loads((ROOT/'qa/x5-method-fingerprints.json').read_text())
X4=json.loads((ROOT/'qa/x4-method-fingerprints.json').read_text())

def methods(path,klass):
    src=path.read_text(encoding='utf-8'); lines=src.splitlines(keepends=True)
    nodes=[n for n in ast.parse(src).body if isinstance(n,ast.ClassDef) and n.name==klass]
    assert len(nodes)==1, (path,klass)
    found={}
    for n in nodes[0].body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            begin=min([n.lineno,*[d.lineno for d in n.decorator_list]])-1
            assert n.name not in found,n.name
            found[n.name]=hashlib.sha256(''.join(lines[begin:n.end_lineno]).encode()).hexdigest()
    return found
for entry in FROZEN['methods']:
    host=methods(ROOT.parent/entry['source'],entry['host_class'])
    if entry['host_class']=='EditorPage':host.update(methods(ROOT/'widgets/editor_lifecycle.py','EditorLifecycleMixin'))
    moved=methods(ROOT.parent/entry['mixin_path'],entry['mixin_class'])
    prefs=methods(ROOT/'widgets/editor_page_preferences.py','EditorPagePreferencesMixin') if entry['host_class']=='EditorPage' else {}
    commands=methods(ROOT/'widgets/editor_page_commands_appearance.py','EditorPageCommandsAppearanceMixin') if entry['host_class']=='EditorPage' else methods(ROOT/'widgets/editor_commands_appearance.py','EditorCommandsAppearanceMixin')
    assert set(moved)==set(entry['extracted_methods']), (entry['host_class'],'moved method inventory')
    assert not set(host)&set(moved), (entry['host_class'],'duplicate method names')
    assert host|moved|prefs|commands==entry['original_methods'],(entry['host_class'],'original method source modified or missing')
# Original frozen x4 host/editor-page method sets remain complete despite their new inherited printing mixins.
original=X4['host_methods']
host=methods(ROOT/'widgets/editor_page.py','EditorPage')
host.update(methods(ROOT/'widgets/editor_lifecycle.py','EditorLifecycleMixin'))
view=methods(ROOT/'widgets/editor_page_search_view.py','EditorPageSearchViewMixin')
printing=methods(ROOT/'widgets/editor_page_printing.py','EditorPagePrintingMixin')
prefs=methods(ROOT/'widgets/editor_page_preferences.py','EditorPagePreferencesMixin')
commands=methods(ROOT/'widgets/editor_page_commands_appearance.py','EditorPageCommandsAppearanceMixin')
assert host|view|printing|prefs|commands==original

# The formerly published aliases must be entirely absent, not merely empty or compatible.
for old in FROZEN['deleted_old_module_shims']:
    assert not (ROOT/pathlib.Path('widgets')/old).exists(), old
assert (ROOT/pathlib.Path('widgets')/'editor_source.py').is_file()
assert (ROOT/pathlib.Path('widgets')/'editor_preview.py').is_file()
# The release must point at canonical imports, never resurrecting old shims.
for file in ['widgets/editor_page.py','widgets/code_editor.py']:
    content=(ROOT/file).read_text()
    for banned in ('from mepynamu.widgets.markopad_source_editor import','from mepynamu.widgets.markopad_preview import'):
        assert banned not in content,(file,banned)
assert 'class MainWindow(EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):' in (ROOT/'widgets/main_window.py').read_text()
assert 'class EditorPage(EditorLifecycleMixin, EditorPageCommandsAppearanceMixin, EditorPagePreferencesMixin, EditorPagePrintingMixin, EditorPageSearchViewMixin, QWidget):' in (ROOT/'widgets/editor_page.py').read_text()

print('PASS x5: exact printing/Properties method identities; no obsolete module aliases; canonical imports retained')
