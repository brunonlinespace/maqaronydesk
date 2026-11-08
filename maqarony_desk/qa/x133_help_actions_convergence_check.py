#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.3: enforce byte-exact Help extraction and untouched x13.2 provenance."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parents[1]
R=P.parent
ref=json.loads((P/'qa/x133-preservation-reference.json').read_text())
base=ref['baseline_sha256_by_path']
OLD='1.0.0-x13.2'
NEW='1.0.0-x13.3'
errors=[]
def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def check(ok,why):
    if not ok:errors.append(why)

metadata={'README.md','suite-pythoine-component.json',
 'maqarony_desk/__init__.py','maqarony_desk/app_constants.py','maqarony_desk/maqaronydesk.json',
 'maqarony_desk/packaging/README.md','maqarony_desk/packaging/fedora/build-appimage.sh',
 'maqarony_desk/packaging/fedora/test-appimage.sh','maqarony_desk/packaging/appimage/maqaronydesk.desktop',
 'maqarony_desk/docs/BUILDING.md','maqarony_desk/docs/README.md'}
history={'maqarony_desk/docs/'+name for name in ('CHANGELOG.md','RELEASE_NOTES.md','RELEASE_CHECKLIST.md')}
arch='maqarony_desk/docs/ARCHITECTURE.md'
appstream='maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml'
main_rel='maqarony_desk/widgets/main_window.py'
mixin_rel='maqarony_desk/widgets/window_parts/help_actions.py'
manifest='maqarony_desk/SOURCE_MANIFEST.sha256'
gate='maqarony_desk/qa/release_check.py'
newfiles={mixin_rel, 'maqarony_desk/qa/x133-preservation-reference.json',
 'maqarony_desk/qa/x133_help_actions_convergence_check.py',
 'maqarony_desk/qa/x133_help_actions_headless_check.py'}
check(ref['baseline_version']==OLD,'wrong frozen predecessor version')
check(ref['baseline_main_window_sha256']==base[main_rel],'wrong predecessor MainWindow hash')
actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file()
 and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
check(actual==set(base)|newfiles,'unexpected files: added='+str(sorted(actual-set(base)-newfiles)[:10])
 +'; missing='+str(sorted(set(base)-actual)[:10]))
changed=metadata|history|{arch,appstream,main_rel,manifest,gate}
for rel,expected in base.items():
    f=R/rel
    check(f.is_file(),'predecessor file missing: '+rel)
    if f.is_file() and rel not in changed:
        check(digest(f.read_bytes())==expected,'existing source or historical record changed: '+rel)
for rel in metadata:
    text=(R/rel).read_text()
    check(NEW in text,'current identity absent: '+rel)
    check(digest(text.replace(NEW,OLD).encode())==base[rel], 'unrelated metadata change: '+rel)
for rel in history:
    content=(R/rel).read_bytes()
    n=ref['historical_document_lengths'][rel]
    check(content.startswith(('# MaqaronyDesk '+NEW).encode()),'new history heading missing: '+rel)
    check(digest(content[-n:])==base[rel], 'previous release history altered: '+rel)
content=(R/arch).read_bytes();n=ref['architecture_prefix_length']
check(digest(content[:n])==base[arch],'architecture history rewritten')

window=(R/main_rel).read_text()
mixin=(R/mixin_rel).read_text()
marker='class HelpActionsMixin:\n'
check(mixin.count(marker)==1,'HelpActionsMixin missing or duplicated')
if marker in mixin:
    body=mixin.split(marker,1)[1]
    divider='    # -- x13.3 extraction boundary between original method groups --\n'
    check(body.count(divider)==1,'Help method groups boundary missing')
    if divider in body:
        first,second=body.split(divider,1)
        check(digest(first.encode())==ref['method_block_1_sha256'],'Quick Tour body changed')
        check(digest(second.encode())==ref['method_block_2_sha256'],'Help method group changed')
        restored=window.replace('from maqarony_desk.widgets.window_parts.help_actions import HelpActionsMixin\n','')
        restored=restored.replace(', HelpActionsMixin,',',')
        first_anchor='    def _current_page(self) -> EditorPage | None:'
        second_anchor='    def eventFilter(self, watched, event) -> bool:'
        check(restored.count(first_anchor)==1 and restored.count(second_anchor)==1,
              'insertion anchors moved')
        restored=restored.replace(first_anchor,first+first_anchor,1)
        restored=restored.replace(second_anchor,second+second_anchor,1)
        check(digest(restored.encode())==base[main_rel],
              'original x13.2 MainWindow not reconstructed byte-for-byte')
    mixast=ast.parse(mixin);winast=ast.parse(window)
    mixcls=next((n for n in mixast.body if isinstance(n,ast.ClassDef)
                 and n.name=='HelpActionsMixin'),None)
    wincls=next((n for n in winast.body if isinstance(n,ast.ClassDef)
                 and n.name=='MainWindow'),None)
    if mixcls and wincls:
        names=[n.name for n in mixcls.body if isinstance(n,ast.FunctionDef)]
        check(names==ref['method_names'] and len(names)==7,'wrong seven Help methods')
        check(not set(names)&{n.name for n in wincls.body if isinstance(n,ast.FunctionDef)},
              'Help methods duplicated in MainWindow')
        check([n.id for n in wincls.bases[:4]]==[
              'DocumentTabsMixin','NavigationHistoryMixin','LayoutControlsMixin','HelpActionsMixin'],
              'mixin inheritance order changed')
        check(all(isinstance(n,ast.FunctionDef) for n in mixcls.body),
              'unexpected Help mixin members')
        for method in ('__init__','_connect_signals','eventFilter','closeEvent'):
            check(method in {n.name for n in wincls.body if isinstance(n,ast.FunctionDef)},
                  'MainWindow ownership changed: '+method)
        check('self.quick_tour_dialog: QWizard | None = None' in window and
              'self.shortcuts_dialog: ShortcutsDialog | None = None' in window and
              'self.about_dialog: AboutDialog | None = None' in window and
              'self._create_tabbed_toolbar()' in window,
              'Qt dialog ownership or Ribbon changed')
    else:check(False,'MainWindow / HelpActionsMixin missing')
app=(R/appstream).read_text()
check('<release version="'+NEW+'"' in app and '<release version="'+OLD+'"' not in app,
      'current-only AppStream identity incorrect')
rg=(R/gate).read_text()
check('x133_help_actions_convergence_check.py' in rg, 'release checker missing x13.3 provenance gate')
check('x133_help_actions_headless_check.py' in rg, 'release checker missing x13.3 headless gate')
if errors:
    print('FAIL x13.3 Help extraction:')
    for x in errors:print('-',x)
    raise SystemExit(1)
print('PASS x13.3: seven byte-exact Help methods; entire x13.2 source / historical records protected')
