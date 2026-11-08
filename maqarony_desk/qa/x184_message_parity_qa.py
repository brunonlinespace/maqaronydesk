#!/usr/bin/env python3
"""Qt-free source-level and executed-operation checks for x18.4 message parity."""
from __future__ import annotations
import ast, hashlib, json, tempfile, os, sys
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1]
reference=json.loads((ROOT/'qa/x184-preservation.json').read_text())
assert reference['baseline']=='1.0.0-x18.3'
for rel,digest in reference['other_production_python'].items():
    assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,('unapproved module',rel)
def ast_methods(rel):
    tree=ast.parse((ROOT/rel).read_text()); methods={}
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            methods.setdefault(node.name,[]).append(node)
    return methods
def method(rel,name,extra=None):
    matches=ast_methods(rel)[name]
    assert len(matches)==1,(rel,name)
    namespace=dict(extra or {})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[matches[0]],type_ignores=[])), f'{rel}:{name}', 'exec'),namespace)
    return namespace[name]
for rel,desc in reference['allowed_changes'].items():
    real=ast_methods(rel)
    assert sorted(real)==desc['original_method_names'],('new/removed methods',rel)
    for name,digests in desc['unchanged'].items():
        actual=[hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in real[name]]
        assert actual==digests,('unapproved method changed',rel,name)

class Signal:
    def __init__(self):self.calls=[]
    def emit(self,*args):self.calls.append(args)
class Bar:
    def __init__(self):self.calls=[]
    def show(self,m,t=0):self.calls.append((m,t))

# PDF: only a newly produced, nonempty, recognizable PDF gets an editor message.
class QFileDialog:
    response=''
    @classmethod
    def getSaveFileName(cls,*a):return cls.response,''
class Printer:
    class PrinterMode:HighResolution=1
    class OutputFormat:PdfFormat=2
    def __init__(self,*a):self.path=None
    def setOutputFormat(self,*a):pass
    def setOutputFileName(self,path):self.path=path
sys.modules['PyQt6']=NS()
sys.modules['PyQt6.QtPrintSupport']=NS(QPrinter=Printer)
pdf=method('widgets/editor_printing.py','_export_pdf_current',{'Path':Path,'QFileDialog':QFileDialog})
with tempfile.TemporaryDirectory() as folder:
    dest=Path(folder)/'paper.pdf'; QFileDialog.response=str(dest)
    bar=Bar(); write=[b'%PDF-1.7\nresult']
    page=NS(module=NS(path=Path(folder)/'note.md'),show_editor_status=bar.show)
    class PageHost:
        def _current_page(self):return page
        def _printable_document(self):return NS(print=lambda printer:dest.write_bytes(write[0]) if write[0] is not None else None)
    host=PageHost();pdf(host)
    assert bar.calls==[(f'Exported PDF to {dest}',4000)],bar.calls
    bar.calls.clear();write[0]=None;pdf(host)
    assert not bar.calls,'Existing unchanged PDF cannot be announced as new export'
    QFileDialog.response='';pdf(host);assert not bar.calls
    QFileDialog.response=str(dest);write[0]=b'notpdf';pdf(host);assert not bar.calls

# Link: target exists -> unchanged open; missing -> local signal.
class URL:
    @staticmethod
    def fromLocalFile(path):return path
    def __init__(self,path):self.path=path
    def scheme(self):return ''
    def isRelative(self):return True
    def toString(self):return self.path
    def isLocalFile(self):return False
class Desktop:
    calls=[]
    @classmethod
    def openUrl(cls,arg):cls.calls.append(arg);return True
link=method('widgets/mwpyn/editor_preview.py','_on_anchor_clicked',{'QDesktopServices':Desktop,'QUrl':URL,'Path':Path})
with tempfile.TemporaryDirectory() as folder:
    target=Path(folder)/'note.md';target.write_text('yes')
    owner=NS(_document_dir=Path(folder),missing_link_requested=Signal(),external_link_requested=Signal())
    link(owner,URL('note.md'));assert Desktop.calls[-1]==str(target)
    link(owner,URL('missing.md'));assert owner.missing_link_requested.calls==[()]
page_source=(ROOT/'widgets/editor_page.py').read_text()
assert 'self.preview.missing_link_requested.connect(' in page_source
assert 'lambda: self.show_editor_status("The linked file could not be found.", 4000)' in page_source

# Insert vs overwrite: actual signal only, original indicator update retained.
mode=method('widgets/editor_page.py','_update_operation_mode')
bar=Bar();updates=[];owner=NS(_update_cursor_position=lambda:updates.append(1),show_editor_status=bar.show)
mode(owner,True);mode(owner,False)
assert bar.calls==[('Overwrite mode enabled.',2500),('Insert mode enabled.',2500)] and len(updates)==2

# External monitor: state transitions only; optional notify defaults to off.
check=method('widgets/editor_lifecycle.py','handle_backing_path_event')
class Backing:
    file_disk_snapshot=NS(digest=b'old')
    _backing_state='normal'
    _loaded_mtime_ns=0
    def __init__(self):self.report=[];self.disk=None
    def _current_disk_snapshot(self):return self.disk
    def _set_backing_state(self,state):self._backing_state=state
    def show_editor_status(self,*args):self.report.append(args)
b=Backing();check(b,notify=True);check(b,notify=True)
assert b.report==[('Backing file missing; the live MaqaronyDesk document remains protected.',6000)]
b.disk=NS(digest=b'changed',state=NS(mtime_ns=3));check(b,notify=True);check(b,notify=True)
assert b.report[-1]==('File changed outside MaqaronyDesk.',5000) and len(b.report)==2
b.disk=NS(digest=b'old',state=NS(mtime_ns=4));check(b,notify=True)
assert b._backing_state=='normal' and len(b.report)==2
b.disk=None;check(b);assert len(b.report)==2,'Internal checks must not emit watcher messages'
life=(ROOT/'widgets/editor_lifecycle.py').read_text()
manager=(ROOT/'controllers/editor_manager.py').read_text()
assert 'self.handle_backing_path_event(notify=True)' in life
assert 'page.handle_backing_path_event(notify=True)' in manager

# Protected version-copy: existing status emitter used exactly once; main adds none.
copy=method('widgets/editor_lifecycle.py','save_copy_to',{})
from types import SimpleNamespace
class Msg:
    class StandardButton:Yes=1;No=2
    @staticmethod
    def question(*a):return 2
    @staticmethod
    def warning(*a):raise AssertionError('unexpected warning')
    @staticmethod
    def critical(*a):raise AssertionError('unexpected critical')
with tempfile.TemporaryDirectory() as folder:
    folder=Path(folder)
    f=folder/'version.md';msgs=Signal()
    owner=NS(_encoded_editor_payload=lambda:b'content',status_message=msgs,
             _save_version_status_override='Saved MaqaronyDesk version as version.md; external disk copy preserved.')
    copy.__globals__.update({'Path':Path,'QMessageBox':Msg,'current_file_state':lambda p: (_ for _ in ()).throw(AssertionError('unexpected existing path')),
                            'FileStateChangedError':type('FileStateChangedError',(Exception,),{}),
                            'tempfile':__import__('tempfile'),'os':os,'fsync_directory':lambda p:None,
                            'install_new_file_from_temp':lambda temporary,destination:temporary.rename(destination)})
    assert copy(owner,f) and f.read_bytes()==b'content'
    assert msgs.calls==[('Saved MaqaronyDesk version as version.md; external disk copy preserved.',)]
    owner._save_version_status_override=None
    f2=folder/'normal.md';assert copy(owner,f2)
    assert msgs.calls[-1]==('Saved as normal.md',)
main=(ROOT/'widgets/main_window.py').read_text()
assert 'page._save_version_status_override = (' in main
assert 'finally:\n                page._save_version_status_override = None' in main
assert 'self.show_status(\n                f"Saved MaqaronyDesk version as' not in main
assert 'page.save_as_file(target)' in main

# Preserve latest editor geometry and x18.2 document-open fix.
assert 'self.editor_status.addPermanentWidget(self.status_indicators_label)' in page_source
assert 'page_layout.setContentsMargins(12, 12, 12, 12)' in page_source
assert 'encoding_status_label.setText' not in life
print('PASS x18.4: five approved outcomes, local routing, no duplicate, transition guard, exact unrelated-code preservation')
