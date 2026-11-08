#!/usr/bin/env python3
"""Qt-free x18.3 editor-message ownership, initial-load and scope regression."""
from __future__ import annotations
import ast, hashlib, json, tempfile
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
record=json.loads((ROOT/'qa/x183-preservation.json').read_text())
assert record['baseline']=='1.0.0-x18.2'
for rel, expected in record['other_production_python'].items():
 assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,('unrelated production changed',rel)

def functions(rel):
 source=(ROOT/rel).read_text()
 tree=ast.parse(source)
 matches={}
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   matches.setdefault(node.name,[]).append(node)
 return source,matches

for rel in ('widgets/editor_page.py','controllers/editor_manager.py','widgets/main_window.py'):
 text, methods=functions(rel)
 expected=record[rel]
 actual={key:[hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in value]
         for key,value in methods.items()}
 for key, digests in expected['unchanged'].items():
  assert actual[key]==digests,('unapproved method change',rel,key)
 assert set(actual)==set(expected['unchanged'])|set(expected['allowed_methods'])

page, page_methods=functions('widgets/editor_page.py')
manager, manager_methods=functions('controllers/editor_manager.py')
main,_=functions('widgets/main_window.py')
assert 'self.status_message.connect(self.show_editor_status)' in page
assert page.index('        self._connect_signals()\n')<page.index('        self.loaded_successfully = self.load_from_disk(show_errors=False)')
assert 'page.status_message.connect(self.status_message)' not in manager
assert 'self.status_message.emit(failure)' in manager
assert 'self.show_status(f"Saved as {target.name}")' not in main
assert 'self.show_status("Place the cursor inside a Markdown link first.")' not in main
assert 'self.show_status("Clipboard HTML is too large to convert safely.")' not in main
for snippet in ('page.show_editor_status("Place the cursor inside a Markdown link first.")',
                'page.show_editor_status("Clipboard HTML is too large to convert safely.")'):
 assert snippet in main
assert 'self.status_message.emit(\n            "Locked Mode enabled." if enabled else "Editing mode enabled."' not in page
for s in ('self.editor_status.showMessage(message, 3000)','self.editor_status.showMessage(message, 4000)'):
 assert s in page
assert 'self.editor_status.addWidget(self.editor_status.message_label, 1)' in page
assert 'self.editor_status.addPermanentWidget(self.status_indicators_label)' in page
assert 'page_layout.setContentsMargins(12, 12, 12, 12)' in page
assert 'page_layout.setSpacing(0)' in page
assert 'root.setSpacing(8)' in page
assert 'self._update_cursor_position()' in (ROOT/'widgets/editor_lifecycle.py').read_text()

# Exercise the real signal-binding method against Qt-free signal doubles.
class Signal:
 def __init__(self): self.connections=[]
 def connect(self,fn): self.connections.append(fn)
 def __call__(self,*args): self.emit(*args)
 def emit(self,*args):
  for fn in self.connections: fn(*args)
class Hub:
 def __init__(self): self.signals={}
 def __getattr__(self,name):
  if name not in self.signals:self.signals[name]=Signal()
  return self.signals[name]
class DummyEditor(Hub):
 def document(self):return self._document
 def __init__(self):super().__init__();self._document=Hub()
class Owner:
 def __init__(self):
  self.editor=DummyEditor();self.repository=Hub();self.content_splitter=Hub()
  self.status_message=Signal();self.messages=[]
  self.module=SimpleNamespace(path=Path('/tmp/source.md'))
 def show_editor_status(self,message,timeout=0): self.messages.append((message,timeout))
 def __getattr__(self,name):return lambda *a,**kw:None
ns={}
method=page_methods['_connect_signals'][0]
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])), '<real signal-binding>', 'exec'),ns)
o=Owner();ns['_connect_signals'](o)
o.status_message.emit('Loaded source.md')
o.editor.paste_rejected.emit('Rejected paste')
assert o.messages==[('Loaded source.md',0),('Rejected paste',0)],o.messages

# Exercise the real failure branch of EditorManager.open_module against fake page/state.
class FakePage:
 loaded_successfully=False
 def __init__(self):
  self.editor_status=SimpleNamespace(message_label=SimpleNamespace(text=lambda:'Could not load missing.md: No such file'))
  self.deleted=False
 def deleteLater(self):self.deleted=True
class FakeState:
 editor_page=None
 def __init__(self):self.cleared=False
 def clear_editor(self):self.cleared=True
class FakeStates:
 def __init__(self):self.state=FakeState()
 def ensure(self,path):return self.state
class Manager:
 def __init__(self):
  self.states=FakeStates();self.status_message=Signal();self.errors=[]
  self.status_message.connect(self.errors.append);self.created=FakePage()
 def _resolve_module(self,value):return value
 def _tabs_enabled(self):return True
 def _create_editor_page(self,module):return self.created
ns={'EditorPage':FakePage}
method=manager_methods['open_module'][0]
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])), '<real open-module>', 'exec'),ns)
m=Manager();file=SimpleNamespace(path=Path('/tmp/missing.md'),loaded=False)
assert ns['open_module'](m,file) is None
assert m.errors==['Could not load missing.md: No such file'],m.errors
assert m.created.deleted and m.states.state.cleared and not file.loaded

# First-load and reload message vocabulary remain the same (no wording updates).
life=(ROOT/'widgets/editor_lifecycle.py').read_text()
for s in ('Could not load {self.module.filename}: {error}',
          'Could not load {self.module.filename}: {message}',
          'Loaded {self.module.filename}',
          'Saved as {destination.name}', 'Saved {self.module.filename}'):
 assert s in life
assert (ROOT/'widgets/editor_page_search_view.py').read_text().count('self.status_message.emit(')>=3
print('PASS x18.3 ownership, initial delivery, failed-open fallback, single-destination routing, layout and exact production preservation')
