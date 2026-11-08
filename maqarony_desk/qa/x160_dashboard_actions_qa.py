#!/usr/bin/env python3
# MaqaronyDesk — current-edition Qt-free QA; historical QA is immutable.
"""Verify x16.0 two-button Dashboard contract against exact issued x15.3."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / 'maqarony_desk'
HERE = Path(__file__).resolve().parent
PRE = json.loads((HERE/'x160-predecessor-fingerprints.json').read_text())
CARD = PKG/'widgets/workspace/dashboard_card.py'
MANAGER = PKG/'controllers/editor_manager.py'
ALLOWED = {
    'README.md','desk-health-check.json','suite-pythoine-component.json',
    'maqarony_desk/__init__.py','maqarony_desk/app_constants.py',
    'maqarony_desk/maqaronydesk.json',
    'maqarony_desk/widgets/workspace/dashboard_card.py',
    'maqarony_desk/controllers/editor_manager.py',
    'maqarony_desk/qa/release_check.py',
    'maqarony_desk/packaging/fedora/build-appimage.sh',
    'maqarony_desk/packaging/fedora/test-appimage.sh',
    'maqarony_desk/packaging/appimage/maqaronydesk.desktop',
    'maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml',
    'maqarony_desk/packaging/README.md',
    'maqarony_desk/docs/RELEASE_NOTES.md',
    'maqarony_desk/docs/CHANGELOG.md',
    'maqarony_desk/docs/README.md',
    'maqarony_desk/docs/BUILDING.md',
    'maqarony_desk/docs/RELEASE_CHECKLIST.md',
}
HISTORICAL_DOC_SUFFIXES = {'maqarony_desk/docs/RELEASE_NOTES.md': (16924, 'cbaa38ccd105b78b9cfb8b6e15dc0ed42711202835b015279cfe736cf5f8c5fc'), 'maqarony_desk/docs/CHANGELOG.md': (55552, '5d0d6015522d7b4f37df1192851dbd1086d183197b0e7d60e2950035c8d6f419'), 'maqarony_desk/docs/RELEASE_CHECKLIST.md': (7015, '764b1b87473171f7f8ba664c6a04bffeef9f8e5152196446fcd4d95f89d45970')}
NEW = {
    'maqarony_desk/qa/x160_dashboard_actions_qa.py',
    'maqarony_desk/qa/x160-predecessor-fingerprints.json',
}


def preservation():
    assert PRE['version'] == '1.0.0-x15.3'
    current = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in ROOT.rglob('*') if p.is_file() and p.name != 'SOURCE_MANIFEST.sha256'
               and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
    old = PRE['files']
    assert set(current)-set(old) == NEW,(set(current)-set(old))-NEW
    assert set(old)-set(current) == set(),set(old)-set(current)
    changed={p for p in old if old[p] != current[p]}
    assert changed <= ALLOWED,sorted(changed-ALLOWED)
    assert {'maqarony_desk/widgets/workspace/dashboard_card.py',
            'maqarony_desk/controllers/editor_manager.py'} <= changed
    # Every historical QA byte is preserved, including the predecessor tester.
    for name in old:
        if '/qa/' in name and name not in {'maqarony_desk/qa/release_check.py'}:
            assert current[name] == old[name],name
    for name in ('maqarony_desk/widgets/workspace/dashboard.py',
                 'maqarony_desk/widgets/workspace/folder_dashboard.py',
                 'maqarony_desk/widgets/main_window.py',
                 'maqarony_desk/widgets/editor_page_search_view.py',
                 'maqarony_desk/widgets/editor_page.py'):
        assert current[name] == old[name],name
    for name, (length, checksum) in HISTORICAL_DOC_SUFFIXES.items():
        content = (ROOT/name).read_bytes()
        assert len(content) > length and hashlib.sha256(content[-length:]).hexdigest() == checksum,name
        assert old[name] != current[name]
    suite = json.loads((ROOT/'suite-pythoine-component.json').read_text())
    health = json.loads((ROOT/'desk-health-check.json').read_text())
    assert suite['version'] == health['application']['version'] == '1.0.0-x16.0'
    assert health['adapter'] == {'id':'maqarony-desk-v1','contract':1}
    for rel,digest in health['source_files'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() == digest,rel
    return changed


def method(tree,name,method_name):
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name == name)
    return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name == method_name)


def dashboard_buttons():
    card_ast=ast.parse(CARD.read_text())
    b=method(card_ast,'DashboardCard','_build_buttons')
    src=ast.unparse(b)
    assert 'self._button(\'Edit\'' in src and 'self._button(\'Preview\'' in src
    assert 'Split View' not in src and 'split_button' not in src
    assert 'self.open_requested.emit(self.module)' in src
    assert 'self.preview_requested.emit(self.module)' in src
    assert 'self.split_requested.emit' not in src
    icons=ast.unparse(method(card_ast,'DashboardCard','refresh_icons'))
    assert "(self.edit_button, 'open')" in icons
    assert "(self.preview_button, 'preview-only')" in icons
    assert 'self.split_button' not in icons
    for name in ('_build_list_layout','_build_grid_layout'):
        s=ast.unparse(method(card_ast,'DashboardCard',name))
        assert '(self.edit_button, self.preview_button)' in s and 'split_button' not in s
    double=ast.unparse(method(card_ast,'DashboardCard','mouseDoubleClickEvent'))
    assert 'self.open_requested.emit(self.module)' in double
    # Card construction executed without importing Qt, verifying exactly two real button instances.
    class Signal:
        def __init__(self):self.callbacks=[]
        def connect(self,f):self.callbacks.append(f)
        def emit(self,*args): pass
    class FakeButton:
        def __init__(self,name):self.name=name;self.clicked=Signal();self.tooltip=''
        def setToolTip(self,t):self.tooltip=t
    def button(text,*,role,grid):
        actual.append((text,role,grid))
        return FakeButton(text)
    cls=ast.ClassDef(name='CardProbe',bases=[],keywords=[],body=[b],decorator_list=[])
    m=ast.Module(body=[cls],type_ignores=[])
    env={};exec(compile(ast.fix_missing_locations(m),str(CARD),'exec'),env)
    for mode in ('list','grid'):
        actual=[];obj=env['CardProbe']();obj._view_mode=mode
        obj._button=button;obj.open_requested=Signal();obj.preview_requested=Signal()
        obj.refresh_icons=lambda:None
        obj.module=object();obj._build_buttons()
        assert [name for name,_,_ in actual] == ['Edit','Preview']
        assert 'last-used editable' in obj.edit_button.tooltip
        assert 'Preview Only' in obj.preview_button.tooltip
        assert len(obj.edit_button.clicked.callbacks) == len(obj.preview_button.clicked.callbacks) == 1
        assert not hasattr(obj,'split_button')
    for theme in ('light','dark'):
        for name in ('open.png','preview-only.png'):
            assert (PKG/'assets/toolbar-icons'/theme/name).is_file()


def editor_routes():
    tree=ast.parse(MANAGER.read_text())
    helper=method(tree,'EditorManager','open_module_for_edit')
    cls=ast.ClassDef(name='ManagerProbe',bases=[],keywords=[],body=[helper],decorator_list=[])
    m=ast.Module(body=[cls],type_ignores=[])
    ns={};exec(compile(ast.fix_missing_locations(m),str(MANAGER),'exec'),ns)
    class Config:
        def __init__(self,values):self.values=values
        def get(self,key,default=None):return self.values.get(key,default)
    for prior,current,expected in [
        ('source','preview','source'),('split','preview','split'),
        ('', 'source','source'),('', 'split','split'),
        ('', 'preview','split'),('garbage','preview','split'),
        ('invalid','source','source')]:
        obj=ns['ManagerProbe']();values={'markopad_last_editable_view_mode':prior,
                                        'markopad_view_mode':current,'lock_editor':True}
        obj.config=Config(values)
        obj.open_module_in_view=lambda module,mode:(module,mode)
        assert obj.open_module_for_edit('file.md') == ('file.md',expected)
        assert values['lock_editor'] is True and values['markopad_view_mode']==current
    editor_text=MANAGER.read_text()
    assert 'self.dashboard.module_open_requested.connect(self.open_module_for_edit)' in editor_text
    assert 'page.module_open_requested.connect(self.open_module_for_edit)' in editor_text
    assert 'self.dashboard.module_preview_requested.connect(lambda module: self.open_module_in_view(module, "preview"))' in editor_text
    assert 'page.module_preview_requested.connect(lambda module: self.open_module_in_view(module, "preview"))' in editor_text
    assert editor_text.count('set_lock_editor(') == 1, 'do not add a lock call'
    assert editor_text.count('module_open_requested.connect(self.open_module_for_edit)') == 2


def predecessor_behaviour():
    # Historical script stays unchanged. Replay only its behavioural checks,
    # not its edition-specific x15.2->x15.3 file preservation assertion.
    p = HERE/'x153_visibility_batch_qa.py'
    spec=importlib.util.spec_from_file_location('historical_x153',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.dashboard_contract()
    mod.flow_contract()


def main():
    changed=preservation()
    dashboard_buttons()
    editor_routes()
    predecessor_behaviour()
    print(f'PASS MaqaronyDesk x16.0: 2-button Dashboard, Edit mode fallback, Preview/lock isolation, historical x15.3 behavioural replay; {len(changed)} approved changed files')

if __name__=='__main__':main()
