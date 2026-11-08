#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.2: verify byte-exact thirteen-method extraction and frozen x13.1 lineage.

Pre-existing historical QA scripts, fingerprints, notes and references stay untouched.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
reference = json.loads((P / 'qa/x132-preservation-reference.json').read_text())
baseline = reference['baseline_sha256_by_path']
OLD = '1.0.0-x13.1'
NEW = '1.0.0-x13.2'
errors = []

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def check(condition: bool, description: str) -> None:
    if not condition:
        errors.append(description)

history = {'maqarony_desk/docs/' + name for name in (
    'CHANGELOG.md', 'RELEASE_NOTES.md', 'RELEASE_CHECKLIST.md')}
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
mixin_rel = 'maqarony_desk/widgets/window_parts/layout_controls.py'
manifest = 'maqarony_desk/SOURCE_MANIFEST.sha256'
release_gate = 'maqarony_desk/qa/release_check.py'
newfiles = {mixin_rel, 'maqarony_desk/qa/x132-preservation-reference.json',
    'maqarony_desk/qa/x132_layout_controls_convergence_check.py',
    'maqarony_desk/qa/x132_layout_controls_headless_check.py'}
check(reference['baseline_version'] == OLD, 'wrong frozen predecessor')
check(reference['baseline_main_window_sha256'] == baseline[main_rel],
      'wrong predecessor MainWindow digest')
for rel, expected in baseline.items():
    f = R / rel
    check(f.is_file(), 'predecessor file missing: ' + rel)
    if not f.is_file():
        continue
    if rel in (metadata | history | {arch, appstream, main_rel, release_gate, manifest}):
        continue
    check(digest(f.read_bytes()) == expected, 'predecessor source/historical record altered: ' + rel)
actual = {p.relative_to(R).as_posix() for p in R.rglob('*')
          if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
check(actual == set(baseline) | newfiles,
      'unexpected added/removed files; additions=' + str(sorted(actual-set(baseline)-newfiles)[:10])
      + ', missing=' + str(sorted(set(baseline)-actual)[:10]))
for rel in metadata:
    text = (R / rel).read_text()
    check(NEW in text, 'current release identity missing: ' + rel)
    check(digest(text.replace(NEW, OLD).encode()) == baseline[rel],
          'unrelated metadata changed: ' + rel)
for rel in history:
    content = (R / rel).read_bytes()
    previous_length = reference['historical_document_lengths'][rel]
    check(content.startswith(('# MaqaronyDesk ' + NEW).encode()),
          'current history heading missing: ' + rel)
    check(digest(content[-previous_length:]) == baseline[rel],
          'existing release history was changed: ' + rel)
content = (R / arch).read_bytes()
length = reference['architecture_prefix_length']
check(digest(content[:length]) == baseline[arch], 'existing architecture text was rewritten')

window = (R / main_rel).read_text()
mixin = (R / mixin_rel).read_text()
marker = 'class LayoutControlsMixin:\n'
check(mixin.count(marker) == 1, 'LayoutControlsMixin missing/duplicated')
if marker in mixin:
    body = mixin.split(marker, 1)[1]
    check(digest(body.encode()) == reference['relocated_method_block_sha256'],
          'layout method bodies or separating whitespace changed')
    restored = window.replace(
        'from maqarony_desk.widgets.window_parts.layout_controls import LayoutControlsMixin\n', '')
    restored = restored.replace(
        'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):',
        'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):')
    anchor = '    def _open_documentation(self) -> None:\n'
    check(restored.count(anchor) == 1, 'Help methods moved or renamed')
    restored = restored.replace(anchor, body + anchor, 1)
    check(digest(restored.encode()) == baseline[main_rel],
          'original x13.1 MainWindow cannot be reconstructed byte-for-byte')

    mix_ast = ast.parse(mixin)
    win_ast = ast.parse(window)
    mix_cls = next((n for n in mix_ast.body if isinstance(n, ast.ClassDef)
                    and n.name == 'LayoutControlsMixin'), None)
    win_cls = next((n for n in win_ast.body if isinstance(n, ast.ClassDef)
                    and n.name == 'MainWindow'), None)
    if mix_cls is not None and win_cls is not None:
        names = [n.name for n in mix_cls.body if isinstance(n, ast.FunctionDef)]
        check(names == reference['extracted_method_names'] and len(names) == 13,
              'wrong set/order of thirteen layout methods')
        check(not set(names) & {n.name for n in win_cls.body if isinstance(n, ast.FunctionDef)},
              'layout methods duplicated in MainWindow')
        check([n.id for n in win_cls.bases[:3]] ==
              ['DocumentTabsMixin', 'NavigationHistoryMixin', 'LayoutControlsMixin'],
              'mixin inheritance order changed')
        check(all('def ' + k + '(' in window for k in
                  ('__init__', '_connect_signals', 'eventFilter', 'closeEvent',
                   '_restore_splitter_geometry', '_show_quick_tour')),
              'Qt ownership, restoration, Help or later Stage 3 methods moved too early')
        check('self._collapsed_mode_restore: dict[str, object] | None = None' in window and
              'self.splitter = QSplitter(' in window and '_create_tabbed_toolbar()' in window,
              'view-state or splitter/action ownership changed')
    else:
        check(False, 'MainWindow or LayoutControlsMixin missing')
check('<release version="' + NEW + '"' in (R / appstream).read_text(),
      'AppStream identity missing')
check('<release version="' + OLD + '"' not in (R / appstream).read_text(),
      'AppStream current-only release contract violated')
check('x132_layout_controls_convergence_check.py' in (R / release_gate).read_text(),
      'current release checker does not invoke x13.2 preservation')
check('x132_layout_controls_headless_check.py' in (R / release_gate).read_text(),
      'current release checker does not invoke x13.2 headless checks')
if errors:
    print('FAIL x13.2 layout-controls extraction:')
    for err in errors:
        print('-', err)
    raise SystemExit(1)
print('PASS x13.2: thirteen byte-exact layout methods extracted; x13.1 source and historical records preserved')
