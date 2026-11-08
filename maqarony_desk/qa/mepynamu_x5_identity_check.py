#!/usr/bin/env python3
"""Dependency-light MepyNamu 0.5.0 identity-rebrand gate."""
from pathlib import Path
import json, hashlib, ast, sys
PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parent
errors=[]
def req(ok,msg):
    if not ok: errors.append(msg)
init=(PKG/'__init__.py').read_text(encoding='utf-8')
constants=(PKG/'app_constants.py').read_text(encoding='utf-8')
launcher=(ROOT/'main.py').read_text(encoding='utf-8')
component=json.loads((ROOT/'suite-pythoine-component.json').read_text(encoding='utf-8'))
manifest=json.loads((PKG/'mepynamu.json').read_text(encoding='utf-8'))
desktop=(PKG/'packaging/appimage/mepynamu.desktop').read_text(encoding='utf-8')
meta=(PKG/'packaging/appimage/io.github.brunonlinespace.mepynamu.metainfo.xml').read_text(encoding='utf-8')
builder=(PKG/'packaging/fedora/build-appimage.sh').read_text(encoding='utf-8')
runtime=(PKG/'services/runtime_paths.py').read_text(encoding='utf-8')
req((ROOT/'mepynamu').is_dir() and not (ROOT/'marko_plus').exists(), 'outer package folder is not mepynamu')
for fragment in ('from mepynamu import APP_NAME, APP_VERSION','from mepynamu.app import main'):
    req(fragment in launcher, f'launcher namespace missing: {fragment}')
for fragment in ('APP_NAME = "MepyNamu"','APP_ID = "mepynamu"','APP_VERSION = "1.0.0-x5.0"','DESKTOP_ID = "mepynamu"'):
    req(fragment in init, f'package identity missing: {fragment}')
for fragment in ('APP_INTERNAL_NAME = "mepynamu"','APP_BRAND_NAME = "MepyNamu"','APP_REVISION = "1.0.0-x5.0"','https://github.com/brunonlinespace/mepynamu'):
    req(fragment in constants, f'constants identity missing: {fragment}')
expected={'id':'mepynamu','name':'MepyNamu','version':'1.0.0-x5.0','desktop_id':'mepynamu','repository':'https://github.com/brunonlinespace/mepynamu','icon':'mepynamu/assets/icons/markopad.png'}
for data,label in ((component,'Suite'),(manifest,'project')):
    for k,v in expected.items():
        if k in data: req(data.get(k)==v, f'{label} identity mismatch: {k}')
for fragment in ('Name=MepyNamu','Exec=mepynamu %f','Icon=mepynamu','StartupWMClass=mepynamu','X-AppImage-Version=1.0.0-x5.0'):
    req(fragment in desktop, f'desktop identity missing: {fragment}')
for fragment in ('io.github.brunonlinespace.mepynamu','<name>MepyNamu</name>','mepynamu.desktop','<binary>mepynamu</binary>','version="1.0.0-x5.0"'):
    req(fragment in meta, f'AppStream identity missing: {fragment}')
for fragment in ('APP_NAME="MepyNamu"','APP_ID="mepynamu"','APP_VERSION="1.0.0-x5.0"','SUITE_DESKTOP_ID="mepynamu"','OUTPUT_STEM="MepyNamu"','usr/lib/mepynamu','usr/bin/mepynamu'):
    req(fragment in builder, f'builder identity missing: {fragment}')
for fragment in ('launcher_root / "mepynamu"','frozen_root / "mepynamu"','Path.home() / ".config" / "mepynamu"','"mepynamu.json"','MepyNamu Workspace'):
    req(fragment in runtime, f'runtime path identity missing: {fragment}')
expected_hashes={'markopad.png': '22a09047102f543744843917d42c76be48cee58b360afb91b6acd2779e9dfd3c', 'markopad.ico': 'de50fb7b2064cd36b0083bab12a03e7df67fa1fc0284c42f9847bef71fe4ee6e', 'markopad-master.png': '9dd0597828ccd04a0ebd2db1ce39dfda9636a114042a4f37add1b9aa2e2b1870', 'markopad-about.png': '4f0258c22404c8016c93f0a57a606be0bd7ef540a4cd4a5ee49b1e2fa7a652e9'}
for name,digest in expected_hashes.items():
    p=PKG/'assets/icons'/name
    req(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest, f'visual asset changed: {name}')
# Current MepyNamu must still vendor the exact rebranded MepySivu engines.
ms_root=Path('/mnt/data/MepySivu-0.3.0-source/mepysivu')
if ms_root.is_dir():
    req((PKG/'widgets/editor_source.py').read_bytes()==(ms_root/'source_editor.py').read_bytes(), 'vendored source editor drifted from MepySivu')
    req((PKG/'widgets/editor_preview.py').read_bytes()==(ms_root/'preview.py').read_bytes(), 'vendored preview drifted from MepySivu')
# Historical internal lineage identifiers intentionally remain.
req('class MarkopadSourceEditor' in (PKG/'widgets/editor_source.py').read_text(), 'historical editor class was unnecessarily renamed')
if errors:
    print('MepyNamu 0.5.0 rebrand check failed:')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('PASS: MepyNamu 0.5.0 identity-rebrand contract')
