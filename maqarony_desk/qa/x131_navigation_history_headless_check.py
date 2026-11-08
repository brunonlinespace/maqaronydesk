#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless exercise of relocated navigation history using a minimal timer stand-in.

Qt GUI lifecycle is not validated by this source-only regression check.
"""
from __future__ import annotations
import ast
from pathlib import Path

P = Path(__file__).resolve().parents[1]
source = (P/'widgets/window_parts/navigation_history.py').read_text()
parsed = ast.parse(source)
cls = next(n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name=='NavigationHistoryMixin')
# Compile precisely the shipped implementation without importing unavailable PyQt6.
class Timer:
    pending=[]
    @classmethod
    def singleShot(cls, delay, fn):
        assert delay==0
        cls.pending.append(fn)
    @classmethod
    def drain(cls):
        while cls.pending:cls.pending.pop(0)()

namespace={'Path':Path,'QTimer':Timer}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(P/'widgets/window_parts/navigation_history.py'),'exec'),namespace)
Mixin=namespace['NavigationHistoryMixin']
class Repository:
    def __init__(self,items):self.items=items
    def get(self,path):return self.items.get(path)
class Manager:
    def __init__(self,window):self.window=window;self.calls=[];self.current_module=None;self.current_folder=None
    def show_dashboard(self):
        self.calls.append(('dashboard',None));self.window._record_dashboard_navigation();return True
    def open_folder(self,path):
        self.calls.append(('folder',path));self.window._record_folder_navigation(path);return object()
    def open_module(self,path):
        self.calls.append(('document',path));self.window._record_module_navigation(type('Module',(),{'path':path})());return object()
class Window(Mixin):
    def __init__(self,root):
        self.library_root=root
        self._navigation_history=[]
        self._navigation_current='dashboard'
        self._navigation_pending=None
        self._navigation_record_scheduled=False
        self._navigation_back_in_progress=False
        self.editor_manager=Manager(self)
        self.repository=Repository({})

import tempfile
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp).resolve()
    folder=root/'docs';folder.mkdir()
    document=folder/'test.md';document.write_text('hello')
    w=Window(root);w.repository.items[document]=object()
    w._record_folder_navigation(folder)
    w._record_module_navigation(type('Module',(),{'path':document})())
    assert len(Timer.pending)==1, 'coalescing should queue one event'
    Timer.drain()
    assert w._navigation_current==f'document:{document}'
    assert w._navigation_history==['dashboard'],w._navigation_history
    # Add a folder record and back; the existing event loop commits once.
    w._record_folder_navigation(folder);Timer.drain()
    assert w._navigation_history==['dashboard',f'document:{document}']
    w._navigate_back()
    assert w.editor_manager.calls==[('document',document)]
    assert not w._navigation_back_in_progress
    assert w._navigation_current==f'document:{document}'
    w._navigate_back()
    assert w.editor_manager.calls[-1]==('dashboard',None)
    # Invalid/outside folders are skipped, and valid historical targets recovered.
    w._navigation_current='folder:'+str(folder)
    w._navigation_history=['dashboard','folder:'+str(root.parent/'outside')]
    w._navigate_back()
    assert w.editor_manager.calls[-1]==('dashboard',None)
    # Bounded history, no duplicate adjacent commit.
    w=Window(root)
    for i in range(70):
        w._queue_navigation_record('document:'+str(root/('a'+str(i))))
        Timer.drain()
    assert len(w._navigation_history)==64
    w._queue_navigation_record(w._navigation_current);Timer.drain()
    assert len(w._navigation_history)==64
    assert not Timer.pending
print('PASS x13.1 navigation history headless: coalescing, Back, skipping invalid folder, history bound')
