#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless exercise of the actual extracted layout methods using Qt stand-ins.

This does not replace testing the live Qt application and AppImage on Fedora KDE.
"""
from __future__ import annotations
import ast
from pathlib import Path

P = Path(__file__).resolve().parents[1]
source = P / 'widgets/window_parts/layout_controls.py'
cls = next(n for n in ast.parse(source.read_text()).body
           if isinstance(n, ast.ClassDef) and n.name == 'LayoutControlsMixin')

class Widget:
    def __init__(self, visible=True): self.visible = visible
    def setVisible(self, value): self.visible = bool(value)
    def isVisible(self): return self.visible

class Action:
    def __init__(self, checked=True): self.checked = bool(checked); self.signals = False
    def blockSignals(self, value): self.signals = bool(value)
    def setChecked(self, value): self.checked = bool(value)
    def isChecked(self): return self.checked

class Splitter:
    def __init__(self, nav, content):
        self.widgets = [nav, content]; self.data = [260, 810]
    def indexOf(self, widget): return self.widgets.index(widget)
    def insertWidget(self, position, widget):
        self.widgets.remove(widget); self.widgets.insert(position, widget)
    def sizes(self): return self.data[:]
    def width(self): return 1078
    def handleWidth(self): return 8
    def setSizes(self, values): self.data = list(values)
    def setStretchFactor(self, index, factor): pass
    def setCollapsible(self, index, value): pass

class Config:
    def __init__(self):
        self.values={'show_status_bar':True,'show_file_header':True,
                     'markopad_tabbed_collapsed':False}; self.writes=[]
    def get(self, key, fallback=None):return self.values.get(key,fallback)
    def set(self,key,value,save=False):
        self.values[key]=value; self.writes.append((key,value,save))

class EditorPage:
    def __init__(self): self.editor_status=Widget(); self.header=True
    def set_header_visible(self, value): self.header=bool(value)

class Ribbon:
    def __init__(self): self._collapsed=False; self.calls=[]
    def set_collapsed(self,value,emit=False):
        self._collapsed=bool(value); self.calls.append((bool(value),emit))

ns={'EditorPage':EditorPage,'SIDEBAR_MINIMUM_WIDTH':205}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(source),'exec'),ns)
Mixin=ns['LayoutControlsMixin']

class Window(Mixin):
    def __init__(self):
        self.navigation=Widget(); self.content_host=Widget()
        self.splitter=Splitter(self.navigation,self.content_host)
        self._restored_sidebar_width=260
        self.sidebar_position_actions={'left':Action(True),'right':Action(False)}
        self.sidebar_action=Action(True); self.status_bar_action=Action(True)
        self.file_header_action=Action(True)
        self.status=Widget()
        self.states=[('/tmp/document.md',type('State',(),{'editor_page':EditorPage()})())]
        self.config=Config(); self.shell_ribbon=Ribbon()
        self._collapsed_mode_restore=None; self.fullscreen=False
    def statusBar(self):return self.status
    def showFullScreen(self):self.fullscreen=True
    def showNormal(self):self.fullscreen=False

w=Window()
assert w._sidebar_position()=='left'
assert w._logical_splitter_sizes()==[260,810]
w._set_sidebar_position('right')
assert w._sidebar_position()=='right'
assert w.sidebar_position_actions['right'].isChecked()
assert w.config.writes[-1]==('sidebar_position','right',True)
assert w._logical_splitter_sizes()[0]==260
w._toggle_sidebar_position()
assert w._sidebar_position()=='left'
assert w.config.writes[-1]==('sidebar_position','left',True)
w._set_splitter_sidebar_width(330)
assert w._logical_splitter_sizes()[0]==330
w._set_sidebar_visible(False)
assert not w.navigation.isVisible() and not w.sidebar_action.isChecked()
w._toggle_sidebar(True)
assert w.navigation.isVisible()
w._set_status_visible(False,persist=True)
assert not w.status.isVisible() and not w.states[0][1].editor_page.editor_status.isVisible()
assert ('show_status_bar',False,True) in w.config.writes
w._set_status_visible(True,persist=True)
w._set_file_header_visible(False,persist=True)
assert not w.states[0][1].editor_page.header
assert ('show_file_header',False,True) in w.config.writes
w._set_file_header_visible(True,persist=True)
assert w.states[0][1].editor_page.header
before=w.config.writes[:]
w._toggle_collapsed_mode(True)
assert not w.navigation.isVisible()
assert not w.status.isVisible()
assert not w.states[0][1].editor_page.header
assert w.shell_ribbon._collapsed
assert w._collapsed_mode_restore is not None
assert w.config.writes==before, 'Focused Mode must not persist transient visibility'
w._toggle_collapsed_mode(False)
assert w.navigation.isVisible() and w.status.isVisible()
assert w.states[0][1].editor_page.header
assert not w.shell_ribbon._collapsed
assert w._collapsed_mode_restore is None
assert w.config.writes==before
w._toggle_fullscreen(True); assert w.fullscreen
w._toggle_fullscreen(False); assert not w.fullscreen
print('PASS x13.2 layout controls headless: sidebar geometry/position, status/header, Focused Mode restoration, fullscreen')
