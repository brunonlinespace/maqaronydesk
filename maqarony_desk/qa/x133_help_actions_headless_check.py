#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.3: execute actual Help methods with headless Qt stand-ins (no PyQt6)."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

P=Path(__file__).resolve().parents[1]
source=(P/'widgets/window_parts/help_actions.py').read_text()
module=ast.parse(source)
cl=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='HelpActionsMixin')

class Signal:
    def __init__(self):self.callbacks=[]
    def connect(self,cb):self.callbacks.append(cb)
    def emit(self,*args):
        for cb in self.callbacks:cb(*args)
class Stub:
    def __init__(self,*args,**kw):
        self.args=args;self.shown=0;self.raised=0;self.activated=0;self.finished=Signal()
        self.toggled=Signal();self.clicked=Signal();self.search=SimpleNamespace(setFocus=lambda *a:None)
    def show(self):self.shown+=1
    def raise_(self):self.raised+=1
    def activateWindow(self):self.activated+=1
    def __getattr__(self,key):
        if key.startswith(('set','add')):return lambda *args,**kwargs:None
        raise AttributeError(key)
class Wizard(Stub):
    WizardStyle=SimpleNamespace(ModernStyle=1)
    WizardOption=SimpleNamespace(NoBackButtonOnStartPage=2,HaveCustomButton1=3)
    WizardButton=SimpleNamespace(CustomButton1=1,Stretch=2,BackButton=3,NextButton=4,FinishButton=5,CancelButton=6)
    def __init__(self,*args):super().__init__(*args);self.pages=[];self.buttons={}
    def addPage(self,page):self.pages.append(page)
    def setButton(self,k,button):self.buttons[k]=button
class Box(Stub):
    def __init__(self,*args):super().__init__(*args);self.value=False
    def setChecked(self,value):self.value=value
class Label(Stub):
    def __init__(self,*args):super().__init__(*args);self.text=args[0] if args else ''
class Button(Stub):pass
class Layout(Stub):pass
class Page(Stub):pass
class Dialog(Stub):pass
class QActions:
    def __init__(self,title,shortcut='',submenu=None):self._title=title;self._shortcut=shortcut;self._submenu=submenu
    def text(self):return self._title
    def menu(self):return self._submenu
    def shortcut(self):return SimpleNamespace(toString=lambda _fmt:self._shortcut)
class Menu:
    def __init__(self,items):self._items=items
    def actions(self):return self._items
class Config:
    def __init__(self):self.data={}
    def get(self,k,default=None):return self.data.get(k,default)
    def set(self,k,val,save=False):self.data[k]=val;self.last=(k,val,save)
class Launcher:
    def __init__(self):self.urls=[]
    def open_url(self,url):self.urls.append(url)
class QMessage:
    calls=[]
    @classmethod
    def information(cls,*args):cls.calls.append(args)
class QTimer:
    @classmethod
    def singleShot(cls,_delay,func):func()

Qt=SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_DeleteOnClose=1),
 TextFormat=SimpleNamespace(RichText=1), AlignmentFlag=SimpleNamespace(AlignLeft=1),
 FocusReason=SimpleNamespace(ShortcutFocusReason=1))
ns={'QWizard':Wizard,'QWizardPage':Page,'QCheckBox':Box,'QPushButton':Button,
    'QVBoxLayout':Layout,'QLabel':Label,'QMessageBox':QMessage,'QTimer':QTimer,
    'ShortcutsDialog':Dialog,'AboutDialog':Dialog,'QAction':QActions,'QMenu':Menu,
    'QKeySequence':SimpleNamespace(SequenceFormat=SimpleNamespace(NativeText=1)),
    'Qt':Qt,'GITHUB_URL':'https://github.com/brunonlinespace/maqaronydesk',
    'ISSUES_URL':'https://github.com/brunonlinespace/maqaronydesk/issues',
    'Path':Path}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cl],type_ignores=[])),str(P/'widgets/window_parts/help_actions.py'),'exec'),ns)
Help=ns['HelpActionsMixin']
class Host(Help):
    def __init__(self):
        self.quick_tour_dialog=None;self.shortcuts_dialog=None;self.about_dialog=None
        self.config=Config();self.desktop_launcher=Launcher()
        self.package_root=P;self.icon_path=P/'assets/icons/maqaronydesk.png'
        self.runtime_paths=SimpleNamespace(package_root=P,config_path=P/'config.json')
        self.pages=[]
        self.menus=[Menu([QActions('Simple','Ctrl+X'),QActions('submenu',submenu=Menu([QActions('Nested','Ctrl+N')])),QActions('None')]) for _ in range(7)]
        for key,value in zip(('file_menu','edit_menu','markdown_menu','insert_menu','view_menu','settings_menu','help_menu'),self.menus):setattr(self,key,value)
        names=('rename_file_action','close_context_action','open_context_tab_action',
               'next_document_tab_action','previous_document_tab_action','toggle_dashboard_view_action',
               'toggle_sidebar_position_action')
        for name in names:setattr(self,name,QActions(name,'Ctrl+K'))
    def windowIcon(self):return 'icon'
    def _current_page(self):return None
    def _tabs_enabled(self):return True
    def _launch_new_window(self,path):self.launched=path

h=Host()
h._show_quick_tour()
w=h.quick_tour_dialog
assert isinstance(w,Wizard) and len(w.pages)==6 and w.shown==1 and w.raised==1
assert len(w.buttons)==1 and len(w.buttons[1].toggled.callbacks)==1
w.buttons[1].toggled.emit(True)
assert h.config.last==('quick_tour_seen',True,True)
h._show_quick_tour();assert h.quick_tour_dialog is w and w.shown==2 and len(w.pages)==6
w.finished.emit(1);assert h.quick_tour_dialog is None
h._show_quick_tour();assert h.quick_tour_dialog is not w
catalog=h._shortcut_catalog()
assert list(catalog)==['File','Edit','Markdown','Insert','View','Settings','Help']
assert ('Nested',h.menus[0]._items[1]._submenu._items[0]) in catalog['File']
assert ('Open Context Tab',h.open_context_tab_action) in catalog['File']
assert ('Next Document Tab',h.next_document_tab_action) in catalog['View']
h._show_shortcuts();d=h.shortcuts_dialog
assert isinstance(d,Dialog) and d.shown==1
h._show_shortcuts();assert h.shortcuts_dialog is d and d.shown==2
d.finished.emit(1);assert h.shortcuts_dialog is None
h._open_documentation();assert h.launched==P/'docs/README.md'
h._open_github();h._open_issues();assert h.desktop_launcher.urls==[ns['GITHUB_URL'],ns['ISSUES_URL']]
h._show_about_dialog();d=h.about_dialog
assert d.args[0]==P/'assets/icons/maqaronydesk-about.png' and d.args[1]==h.runtime_paths.config_path
h._show_about_dialog();assert h.about_dialog is d and d.shown==2
d.finished.emit(1);assert h.about_dialog is None
print('PASS x13.3 headless Help methods: Quick Tour, preference, 7 menu groups, shortcuts, links, docs and About lifecycle')
