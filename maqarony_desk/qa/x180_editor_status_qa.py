#!/usr/bin/env python3
"""x18.0 editor status only; retain workspace status and historical editor methods."""
from pathlib import Path
import ast,hashlib,json
PKG=Path(__file__).resolve().parents[1]
page=(PKG/'widgets/editor_page.py').read_text();view=(PKG/'widgets/editor_page_search_view.py').read_text();prefs=(PKG/'widgets/editor_page_preferences.py').read_text();life=(PKG/'widgets/editor_lifecycle.py').read_text();main=(PKG/'widgets/main_window.py').read_text()
assert 'class EditorMessageStatusBar(QStatusBar)' in page
assert 'self.editor_status.setSizeGripEnabled(False)' in page
assert 'root.setContentsMargins(12, 12, 12, 0)' in page
assert 'self.position_label' in page and 'Chars {total_chars:,}' in page
assert 'Char {cursor.position()}' not in page
assert 'self.editor.textChanged.connect(self._update_cursor_position)' in page
assert 'self.editor_status.addPermanentWidget(self.encoding_status_label)' not in page
assert 'self.editor_status.showMessage(' in page
assert 'self.view_status_label.setText(f"{view} {zoom}%")' in page
assert 'self.encoding_status_label.setText(f"{self.file_encoding.upper()} {newline}")' in page
assert 'self._update_cursor_position()' in view and 'self.set_view_mode(self.view_mode, persist=False)' in prefs and 'self._update_cursor_position()' in life
assert 'status = QStatusBar(self)' in main
assert 'self.statusBar().showMessage(' in main or 'def show_status(' in main
order=['self.editor_status.addWidget(self.operation_mode_label)','self.editor_status.addWidget(self.position_label, 3)','self.editor_status.addWidget(self.view_status_label)','self.editor_status.addWidget(self.encoding_status_label)','self.editor_status.addWidget(self.editor_status.message_label, 1)']
assert list(map(page.index,order))==sorted(map(page.index,order))
# Live source method, executed without PyQt6 imports.
tree=ast.parse(page);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorPage')
m=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_update_cursor_position')
method=ast.FunctionDef(name='update',args=m.args,body=m.body,decorator_list=[],returns=m.returns,type_comment=None)
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<desk-status>','exec'),ns)
class Label:
 def setText(self,t):self.text=t
 def setToolTip(self,t):self.tooltip=t
class Cursor:
 def blockNumber(self):return 6
 def positionInBlock(self):return 17
class Editor:
 def textCursor(self):return Cursor()
 def toPlainText(self):return 'a'*1240
 def blockCount(self):return 109
class Config:
 def get_int(self,name,default,**kw):return 110
class Owner:
 editor=Editor();config=Config();view_mode='split';file_encoding='utf-8';file_newline='\r\n'
 position_label=Label();view_status_label=Label();encoding_status_label=Label()
o=Owner();ns['update'](o)
assert o.position_label.text=='Ln 7/109 Col 18 Chars 1,240'
assert o.view_status_label.text=='Split 110%'
assert o.encoding_status_label.text=='UTF-8 CRLF'
record=json.loads((PKG/'qa/x180-method-preservation.json').read_text())['unchanged_methods']
for key,oldhashes in record.items():
 f,name=key.split('::');src=ast.parse((PKG/f).read_text());hashes=[hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in ast.walk(src) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert hashes==oldhashes,('unexpected editor method change',key)
assert 'return "\\r\\n"' in life and 'if crlf >= cr and crlf >= lf and crlf:' in life  # x17.2 newline policy
assert 'if self.view_mode == "preview":' in view  # x17.0 replacement guard
print('PASS x18.0 editor status, geometry contract, events, numeric formatting, historical method preservation')
