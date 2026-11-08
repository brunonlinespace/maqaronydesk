#!/usr/bin/env python3
"""Qt-free corrective x18.1 editor-status contract and preservation gate."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'widgets/editor_page.py').read_text()
record=json.loads((ROOT/'qa/x181-method-preservation.json').read_text())
assert 'page_layout.setContentsMargins(12, 12, 12, 12)' in src
assert 'page_layout.setSpacing(0)' in src
assert 'root.setSpacing(8)' in src
assert 'page_layout.addLayout(root, 1)' in src
assert 'page_layout.addWidget(self.editor_status, 0)' in src
assert 'root.addWidget(self.editor_status' not in src
assert 'self.editor_status.setSizeGripEnabled(False)' in src
assert 'self.editor_status.addWidget(self.editor_status.message_label, 1)' in src
assert 'self.editor_status.addPermanentWidget(self.status_indicators_label)' in src
assert 'status_indicators_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)' in src
assert 'status_indicators_label.setMinimumWidth(0)' in src
for old in ('position_label','operation_mode_label','view_status_label','encoding_status_label'):
 assert 'self.'+old not in src,old
nodes=[n for n in ast.walk(ast.parse(src)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
by={}
for n in nodes:
 name=n.name
 k=name if name not in by else name+'#'+str(sum(t==name or t.startswith(name+'#') for t in by))
 by[k]=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()
for k,v in record['unchanged_method_hashes'].items():assert by[k]==v,('modified unrelated method',k)
cls=next(n for n in ast.parse(src).body if isinstance(n,ast.ClassDef) and n.name=='EditorPage')
m=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_update_cursor_position')
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[m],type_ignores=[])),'<desk-status>','exec'),ns)
class Label:
 def setText(self,t):self.text=t
 def setToolTip(self,t):self.tooltip=t
class Cursor:
 def blockNumber(self):return 19
 def positionInBlock(self):return 17
class Editor:
 def textCursor(self):return Cursor()
 def toPlainText(self):return 'x'*4842
 def blockCount(self):return 109
 def overwriteMode(self):return False
class Config:
 def get_int(self,*args,**kw):return 100
class Owner:
 editor=Editor();config=Config();view_mode='split';file_encoding='utf-8';file_newline='\r\n'
 status_indicators_label=Label()
o=Owner();ns['_update_cursor_position'](o)
assert o.status_indicators_label.text=='Insert · Ln 20/109 Col 18 Chars 4,842 · UTF-8 CRLF · Split 100%',o.status_indicators_label.text
assert o.status_indicators_label.tooltip==o.status_indicators_label.text
o.editor.overwriteMode=lambda:True;o.view_mode='preview';o.config.get_int=lambda *args,**kw:300
ns['_update_cursor_position'](o)
assert o.status_indicators_label.text.startswith('Overwrite ·')
assert o.status_indicators_label.text.endswith('· Preview 300%')
# Retained file safety, Preview Only and mixed-newline contracts.
assert 'if self.view_mode == "preview":' in (ROOT/'widgets/editor_page_search_view.py').read_text()
assert 'if crlf >= cr and crlf >= lf and crlf:' in (ROOT/'widgets/editor_lifecycle.py').read_text()
assert 'status = QStatusBar(self)' in (ROOT/'widgets/main_window.py').read_text()
print('PASS x18.1 two-label status, accurate grouped indicators, geometry and protected methods')
