#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.1: check exact x13.0 preservation and six-method history extraction.

Never rewrite historical source-reference files or previous-edition QA.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
reference = json.loads((P / 'qa/x131-preservation-reference.json').read_text())
baseline = reference['baseline_sha256_by_path']
OLD = '1.0.0-x13.0'
NEW = '1.0.0-x13.1'
errors = []
def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
def check(condition, description):
    if not condition:
        errors.append(description)

history = {'maqarony_desk/docs/' + k for k in
           ('CHANGELOG.md', 'RELEASE_NOTES.md', 'RELEASE_CHECKLIST.md')}
metadata = {'README.md', 'suite-pythoine-component.json',
    'maqarony_desk/__init__.py', 'maqarony_desk/app_constants.py',
    'maqarony_desk/maqaronydesk.json', 'maqarony_desk/packaging/README.md',
    'maqarony_desk/packaging/fedora/build-appimage.sh',
    'maqarony_desk/packaging/fedora/test-appimage.sh',
    'maqarony_desk/packaging/appimage/maqaronydesk.desktop',
    'maqarony_desk/docs/BUILDING.md', 'maqarony_desk/docs/README.md'}
arch = 'maqarony_desk/docs/ARCHITECTURE.md'
appstream = 'maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml'
main_rel = 'maqarony_desk/widgets/main_window.py'
mixin_rel = 'maqarony_desk/widgets/window_parts/navigation_history.py'
manifest = 'maqarony_desk/SOURCE_MANIFEST.sha256'
release_gate = 'maqarony_desk/qa/release_check.py'
newfiles = {mixin_rel, 'maqarony_desk/qa/x131-preservation-reference.json',
            'maqarony_desk/qa/x131_navigation_history_convergence_check.py',
            'maqarony_desk/qa/x131_navigation_history_headless_check.py'}
check(reference['baseline_version']==OLD,'wrong frozen predecessor')
check(reference['baseline_main_window_sha256']==baseline[main_rel], 'wrong predecessor MainWindow digest')
for rel, expected in baseline.items():
    f=R/rel
    check(f.is_file(), 'predecessor file missing: '+rel)
    if not f.is_file(): continue
    if rel in (metadata | history | {arch, appstream, main_rel, release_gate, manifest}):
        continue
    check(digest(f.read_bytes())==expected, 'original source or historical record changed: '+rel)
actual = {p.relative_to(R).as_posix() for p in R.rglob('*')
          if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
check(actual==set(baseline)|newfiles,
      'unexpected added/removed files; additions='+str(sorted(actual-set(baseline)-newfiles)[:10])+', removed='+str(sorted(set(baseline)-actual)[:10]))
for rel in metadata:
    now=(R/rel).read_text()
    check(NEW in now, 'new identity missing: '+rel)
    check(digest(now.replace(NEW, OLD).encode())==baseline[rel],
          'metadata unrelated to identity altered: '+rel)
for rel in history:
    now=(R/rel).read_bytes()
    length=reference['historical_document_lengths'][rel]
    check(now.startswith(('# MaqaronyDesk '+NEW).encode()),'current history header missing: '+rel)
    check(digest(now[-length:])==baseline[rel], 'historical text not intact as suffix: '+rel)
content=(R/arch).read_bytes()
length=reference['architecture_prefix_length']
check(digest(content[:length])==baseline[arch], 'existing architecture text rewritten')

# Exact MainWindow byte reproduction, restoring only the approved extraction.
window=(R/main_rel).read_text()
mixin=(R/mixin_rel).read_text()
marker='class NavigationHistoryMixin:\n'
check(mixin.count(marker)==1,'NavigationHistoryMixin missing or duplicated')
if marker in mixin:
    body=mixin.split(marker,1)[1]
    check(digest(body.encode())==reference['relocated_method_block_sha256'],
          'navigation method bytes changed')
    restored=window.replace('from maqarony_desk.widgets.window_parts.navigation_history import NavigationHistoryMixin\n','')
    restored=restored.replace(
        'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):',
        'class MainWindow(DocumentTabsMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):')
    original_anchor='    def eventFilter(self, watched, event) -> bool:\n'
    check(restored.count(original_anchor)==1,'eventFilter moved or changed')
    restored=restored.replace(original_anchor,body+original_anchor,1)
    check(digest(restored.encode())==baseline[main_rel], 'x13.0 MainWindow not exactly reconstructable')
    m=ast.parse(mixin)
    w=ast.parse(window)
    c=next((n for n in m.body if isinstance(n,ast.ClassDef) and n.name=='NavigationHistoryMixin'),None)
    wc=next((n for n in w.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow'),None)
    if c is not None and wc is not None:
        names=[n.name for n in c.body if isinstance(n, ast.FunctionDef)]
        check(names==reference['extracted_method_names'] and len(names)==6, 'not exactly six agreed methods')
        check(not set(names)&{n.name for n in wc.body if isinstance(n,ast.FunctionDef)},
              'duplicate history method remains in MainWindow')
        check([n.id for n in wc.bases[:2]]==['DocumentTabsMixin','NavigationHistoryMixin'],
              'mixin inheritance order changed')
        check('def eventFilter(' in window and 'self._navigate_back()' in window,
              'event filter/Back routing changed')
        check('self._navigation_history: list[str] = []' in window and
              'self._navigation_back_in_progress = False' in window,
              'history-state ownership changed')
        check('def _toggle_collapsed_mode(' in window and 'def _show_quick_tour(' in window,
              'later Stage 3 work moved early')
        check('class DocumentTabsMixin' in (P/'widgets/window_parts/document_tabs.py').read_text(),
              'x13.0 Document Tabs extraction unexpectedly changed')
    else:
        check(False,'MainWindow or NavigationHistoryMixin missing')
check((R/appstream).read_text().count('<release version="'+NEW+'"')==1,
      'AppStream current identity missing')
check('<release version="'+OLD+'"' not in (R/appstream).read_text(),
      'AppStream current-only policy violated')
check('x131_navigation_history_convergence_check.py' in (R/release_gate).read_text(),
      'release gate does not invoke x13.1 preservation')
check('x131_navigation_history_headless_check.py' in (R/release_gate).read_text(),
      'release gate does not invoke navigation headless checks')
if errors:
    print('FAIL x13.1 source preservation/navigation-history extraction:')
    for e in errors:print('-',e)
    raise SystemExit(1)
print('PASS x13.1: six byte-exact navigation methods moved; complete x13.0 baseline and historical records preserved')
