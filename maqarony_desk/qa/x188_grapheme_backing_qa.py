#!/usr/bin/env python3
"""x18.8 release gate: strict predecessor preservation + scoped Qt-free behavior tests."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "maqarony_desk"
reference = json.loads((PACKAGE / "qa/x188-baseline-integrity.json").read_text())
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def method_ast(text):
    found={}
    def walk(nodes,prefix=""):
        for n in nodes:
            if isinstance(n,ast.ClassDef): walk(n.body,prefix+n.name+".")
            elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                found[prefix+n.name]=sha(ast.dump(n,include_attributes=False).encode())
    walk(ast.parse(text).body)
    return found

for rel,digest in reference["untouched_sha256"].items():
    path=ROOT/rel
    assert path.is_file() and sha(path.read_bytes()) == digest, f"Unauthorized source/asset change: {rel}"
for rel,unchanged in reference["unchanged_method_asts"].items():
    current=method_ast((ROOT/rel).read_text())
    changed=set(reference["allowed_changed_methods"][rel])
    added=set(reference["allowed_new_methods"].get(rel,[]))
    assert set(current)==set(unchanged)|changed|added,(rel,sorted(set(current)^set(unchanged)))
    for m,digest in unchanged.items():
        assert current[m]==digest, f"Unrelated method modified: {rel}:{m}"
assert not list(ROOT.rglob("*.svg")), 'SVG asset was unexpectedly introduced'
assets=list((PACKAGE/'assets').rglob('*.png'))
assert len(assets)==256,(len(assets),'PNG count changed')
assert 'self.handle_backing_path_event(notify=True)' in (PACKAGE/'widgets/editor_lifecycle.py').read_text()
assert 'page.handle_backing_path_event(notify=True)' in (PACKAGE/'controllers/editor_manager.py').read_text()
assert 'len(self.editor.toPlainText())' not in (PACKAGE/'widgets/editor_page.py').read_text()

# Build a Qt-interface double. The actual production code calls Qt's grapheme
# boundary finder; this tests the counting protocol, not native Qt behavior.
try:
    import regex
    graphemes=lambda text:regex.findall(r"\X",text)
except ImportError:
    def graphemes(text):
        result=[]
        for c in text:
            if result and (unicodedata.combining(c) or c=='\ufe0f' or c=='\u200d' or result[-1].endswith('\u200d')):
                result[-1]+=c
            else:result.append(c)
        return result
class Data: pass
class Finder:
    class BoundaryType: Grapheme='g'
    calls=0
    def __init__(self,kind,text):
        assert kind=='g'
        type(self).calls+=1
        self.terms=graphemes(text)
        self.at=0
    def toNextBoundary(self):
        self.at+=1
        return self.at if self.at<=len(self.terms) else -1
class Block:
    def __init__(self,text):self.content=text;self.rev=0;self.ud=None;self.succ=None
    def isValid(self):return True
    def text(self):return self.content
    def revision(self):return self.rev
    def userData(self):return self.ud
    def setUserData(self,data):self.ud=data
    def next(self):return self.succ or Invalid()
class Invalid:
    def isValid(self):return False
class Document:
    def __init__(self,lines):
        self.blocks=[Block(x) for x in lines]
        for a,b in zip(self.blocks,self.blocks[1:]):a.succ=b
    def begin(self):return self.blocks[0]
    def edit(self,i,value):self.blocks[i].content=value;self.blocks[i].rev+=1
modsys=types.ModuleType('PyQt6'); qtcore=types.ModuleType('PyQt6.QtCore');qtgui=types.ModuleType('PyQt6.QtGui')
qtcore.QTextBoundaryFinder=Finder;qtgui.QTextBlockUserData=Data
old={n:sys.modules.get(n) for n in ['PyQt6','PyQt6.QtCore','PyQt6.QtGui']}
try:
    sys.modules.update({'PyQt6':modsys,'PyQt6.QtCore':qtcore,'PyQt6.QtGui':qtgui})
    spec=importlib.util.spec_from_file_location('x188_count',PACKAGE/'widgets/mwpyn/character_count.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
finally:
    for n,v in old.items():
        if v is None:sys.modules.pop(n,None)
        else:sys.modules[n]=v
count=module.count_markdown_characters
cases=[([''],0),(['**Hello**'],9),(['e\u0301'],1),(['\U0001f600'],1),(['\U0001f469\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466'],1),(['Hello',''],6),(['',''],1),(['a','','b'],4),(['# H','\u0928\u092e\u0938\u094d\u0924\u0947'],3+1+len(graphemes('\u0928\u092e\u0938\u094d\u0924\u0947')))]
for lines,total in cases: assert count(Document(lines))==total,(lines,count(Document(lines)),total)
doc=Document(['**abc**','e\u0301','\U0001f600'])
Finder.calls=0; assert count(doc)==7+1+1+1+1
calls=Finder.calls
for _ in range(5):assert count(doc)==11
assert Finder.calls==calls, 'unchanged blocks recounted'
doc.edit(1,'e\u0301!')
assert count(doc)==12
assert Finder.calls==calls+1, 'modified block not invalidated precisely'

# Dynamically extract only the actual production methods under test.
def extract(path,cls,name):
    tree=ast.parse(path.read_text())
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    n=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return n
convsrc=(PACKAGE/'widgets/message_conventions.py').read_text()
conv={}
exec(compile(ast.parse(convsrc),'<conventions>','exec'),conv)

class Label:
    def __init__(self):self.value=''
    def setText(self,v):self.value=v
    def setToolTip(self,v):pass
    def clear(self):self.value=''
    def text(self):return self.value
class Timer:
    def __init__(self):self.ms=None
    def stop(self):self.ms=None
    def start(self,n):self.ms=n
class Widget:
    def __init__(self):self.visible=False;self.enabled=None;self.value=''
    def show(self):self.visible=True
    def hide(self):self.visible=False
    def setText(self,t):self.value=t
    def setEnabled(self,v):self.enabled=v

def compiled(path,cls,name,extra):
    n=extract(path,cls,name)
    ns=dict(extra)
    exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),ns)
    return ns[name]
pagepath=PACKAGE/'widgets/editor_page.py';lifepath=PACKAGE/'widgets/editor_lifecycle.py'
baseenv={**conv,'DEFAULT_MESSAGE_DURATION_MS':4000}
show=compiled(pagepath,'EditorMessageStatusBar','showMessage',baseenv)
clear=compiled(pagepath,'EditorMessageStatusBar','clearMessage',baseenv)
show_local=compiled(pagepath,'EditorPage','show_editor_status',baseenv)
state=compiled(lifepath,'EditorLifecycleMixin','_set_backing_state',{})
event=compiled(lifepath,'EditorLifecycleMixin','handle_backing_path_event',{})
class Status:
    def __init__(self):self.message_label=Label();self._message_timer=Timer();self.sent=[]
    def showMessage(self,message,timeout=4000,*,warning_id=None):
        self.sent.append((message,warning_id))
        return show(self,message,timeout,warning_id=warning_id)
    def clearMessage(self,*,warning_id=None):return clear(self,warning_id=warning_id)
class Page:
    show_editor_status=show_local
    _set_backing_state=state
    handle_backing_path_event=event
    def __init__(self):
        self.editor_status=Status();self.external_banner=Widget();self.external_label=Widget();self.reload_external_button=Widget()
        self._backing_state='normal';self.file_disk_snapshot=types.SimpleNamespace(digest=b'a')
        self.disk=self.file_disk_snapshot;self.module=types.SimpleNamespace(path='test.md')
        self._loaded_mtime_ns=0
    def _current_disk_snapshot(self):return self.disk
    def _refresh_header(self):pass
p=Page();s=p.editor_status
p.disk=None;p.handle_backing_path_event(notify=True)
assert s._warning_id=='backing_file' and s._critical_editor_message and p.external_banner.visible
assert len(s.sent)==1
p.handle_backing_path_event(notify=True);assert len(s.sent)==1,'repeated state generated repeated warning'
s.showMessage('Could not save document.md: permission denied.')
assert s._warning_id is None and s._critical_editor_message
p.disk=types.SimpleNamespace(digest=b'a',state=types.SimpleNamespace(mtime_ns=7))
p.handle_backing_path_event(notify=True)
assert p._backing_state=='normal' and s._critical_editor_message and s.message_label.text().startswith('Could not save')
s.clearMessage();p.disk=types.SimpleNamespace(digest=b'b',state=types.SimpleNamespace(mtime_ns=8))
p.handle_backing_path_event(notify=True)
assert s._warning_id=='backing_file' and p.external_banner.visible and len(s.sent)==3
p.disk=types.SimpleNamespace(digest=b'a',state=types.SimpleNamespace(mtime_ns=9))
p.handle_backing_path_event(notify=True)
assert s.message_label.text()=='' and s._warning_id is None and not p.external_banner.visible
s.showMessage('Could not load document.md.')
p._set_backing_state('missing');p._set_backing_state('normal')
assert s.message_label.text().startswith('Could not load')
s.clearMessage();s.showMessage('File changed outside MaqaronyDesk.',warning_id='backing_file')
s.showMessage('Saved document.md.')
assert s._warning_id is None and not s._critical_editor_message  # retained x18.7 success handling
s.showMessage('Routine operation complete.')
assert s._message_timer.ms==4000
print('PASS: x18.8 scoped source + PNG preservation, Unicode Chars cache, backing warning identity and transition deduplication')
