#!/usr/bin/env python3
"""x21.6: ensure full QA relocation and active release coverage."""
from pathlib import Path
import json, hashlib
root = Path(__file__).resolve().parents[1]
qa = root / 'qa'
ref = json.loads((qa / 'x216-relocation-origin.json').read_text())
assert len(ref['old_tools_files']) == 167
assert not (root / 'tools').exists(), 'Obsolete tools/ directory remains'
assert all((qa / name).is_file() for name in ref['old_tools_files']), 'Previously tracked QA script or reference missing'
for name, before in ref['old_tools_files'].items():
    path = qa / name
    if path.suffix == '.json':
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before, name
runner = (qa / 'release_check.py').read_text()
builder = (root / 'packaging/fedora/build-appimage.sh').read_text()
assert '$PROGRAM_ROOT/qa/release_check.py' in builder
assert '$PROGRAM_ROOT/tools/release_check.py' not in builder
for script in ('x210_toolbar_icons_qa.py', 'x213_icon_family_qa.py',
               'x212_exit_toolbar_qa.py', 'x211_icon_wiring_qa.py',
               'x133_help_actions_headless_check.py', 'x131_navigation_history_headless_check.py',
               'x132_layout_controls_headless_check.py', 'x121_direct_drop_check.py'):
    assert ('"qa" / "' + script + '"') in runner, script
print('PASS x21.6 QA migration: 167 moved; 35 reference JSON preserved; active gate and builder retargeted')
