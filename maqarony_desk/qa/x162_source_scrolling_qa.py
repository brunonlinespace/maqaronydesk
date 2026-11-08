#!/usr/bin/env python3
"""x16.2 source-scroll-only corrective on frozen x16.0 Dashboard baseline."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import importlib.util

_here=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('previous_x160_dashboard_actions',_here/'x160_dashboard_actions_qa.py')
previous=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(previous)

ROOT=Path(__file__).resolve().parents[2]
PKG=ROOT/'maqarony_desk'
source=PKG/'widgets/mwpyn/editor_source.py'
old='        self.setCenterOnScroll(True)'
new='        self.setCenterOnScroll(False)'


def run():
    text=source.read_text(encoding='utf-8')
    assert text.count(new)==1 and old not in text
    # Exactly restore the x15.3 source editor bytes, which x16.0 preserved unchanged.
    expected=previous.PRE['files']['maqarony_desk/widgets/mwpyn/editor_source.py']
    assert hashlib.sha256(text.replace(new,old).encode('utf-8')).hexdigest()==expected
    current={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in ROOT.rglob('*') if p.is_file() and p.name != 'SOURCE_MANIFEST.sha256'
             and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
    original=previous.PRE['files']
    new_files=previous.NEW|{'maqarony_desk/qa/x162_source_scrolling_qa.py'}
    assert set(current)-set(original)==new_files,(set(current)-set(original))-new_files
    assert set(original)-set(current)==set(),set(original)-set(current)
    allowed=previous.ALLOWED|{'maqarony_desk/widgets/mwpyn/editor_source.py','maqarony_desk/docs/QA.md'}
    changed={p for p in original if original[p]!=current[p]}
    assert changed <= allowed,sorted(changed-allowed)
    assert 'maqarony_desk/widgets/mwpyn/editor_source.py' in changed
    for name in original:
        if '/qa/' in name and name != 'maqarony_desk/qa/release_check.py':
            assert current[name]==original[name],name
    for name,(length,checksum) in previous.HISTORICAL_DOC_SUFFIXES.items():
        content=(ROOT/name).read_bytes()
        assert len(content)>length and hashlib.sha256(content[-length:]).hexdigest()==checksum,name
    suite=json.loads((ROOT/'suite-pythoine-component.json').read_text())
    health=json.loads((ROOT/'desk-health-check.json').read_text())
    assert suite['version']==health['application']['version']=='1.0.0-x16.2'
    assert health['adapter']=={'id':'maqarony-desk-v1','contract':1}
    for path,digest in health['source_files'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    previous.dashboard_buttons()
    previous.editor_routes()
    previous.predecessor_behaviour()
    print('PASS x16.2: one-line scroll correction, historical integrity, x16.0 Dashboard behavior')

if __name__=='__main__': run()
