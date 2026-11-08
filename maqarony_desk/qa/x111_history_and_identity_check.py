#!/usr/bin/env python3
"""x11.1 full-identity and exact normalized production preservation gate.
Original x1-x10 scripts/fixtures remain archived unmodified. All production
Python ASTs are compared against the original x10 snapshot after reversing
*only* the approved identity substitutions; no method fingerprint is updated.
"""
import ast,hashlib,json,os,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]; ROOT=R.parent
F=json.loads((R/'qa/x11-preservation-reference.json').read_text())
errors=[]
def req(ok,message):
    if not ok: errors.append(message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def norm(s):
    s=s.replace('app.setApplicationName(APP_DISPLAY_NAME)','app.setApplicationName(APP_INTERNAL_NAME)')
    for a,b in (
        ('maqaronydesk-about.png','markopad-about.png'),
        ('maqaronydesk-master.png','markopad-master.png'),
        ('maqaronydesk.ico','markopad.ico'),
        ('maqaronydesk.png','markopad.png'),
        ('MaqaronyDesk','MepyNamu'),('MaqaronyPad','MepySivu'),('MAQARONYDESK','MEPYNAMU'),
        ('maqaronydesk','mepynamu'),('maqarony_desk','mepynamu'),
        ('1.0.0-x11.1','1.0.0-x10.0'),
    ):s=s.replace(a,b)
    return s
actual=set()
for file in R.rglob('*.py'):
    rel=file.relative_to(R).as_posix()
    if rel.startswith('qa/'):continue
    actual.add(rel)
    try:
        fingerprint=sha(ast.dump(ast.parse(norm(file.read_text())),include_attributes=False).encode())
        req(fingerprint==F['production_ast'].get(rel),'production AST drift: '+rel)
    except (OSError,SyntaxError,UnicodeError) as exc: errors.append(f'AST parse {rel}: {exc}')
req(actual==set(F['production_ast']), 'production Python inventory changed')
# Immutable predecessor/fingerprint verification from x11.0 reference, except the
# two historically corrupted active passages restored from original 0.4.17.
for key in ("ribbon_sha256","historical_sha256","artwork_sha256"):
    for rel,expected in F[key].items():
        if rel in ("docs/CHANGELOG.md","docs/RELEASE_NOTES.md"): continue
        p=R/rel
        req(p.is_file() and sha(p.read_bytes())==expected, f"{key} modified: {rel}")
for rel,expected in F["historical_prefix_sha256"].items():
    original_archive=R/"docs/history"/("MepyNamu-1.0.0-x10.0-"+rel.rsplit("/",1)[1])
    req(original_archive.is_file() and sha(original_archive.read_bytes())==expected,
        "original MepyNamu x10 source history modified: "+rel)
for rel,expected_digest in (
    ("CHANGELOG.md", "fda1fd314832022492663cd2d8110e592e54f97cdbfd031b57a88f751b0f9d03"),
    ("RELEASE_NOTES.md", "4b0a5ff11b33d005ff83b92bffc0f19d428cd4804e5df4073120e8b963cfe5e7"),
):
    archived=R/"docs/history"/("Marko-Plus-0.4.17-"+rel)
    live=R/"docs"/rel
    req(archived.is_file() and sha(archived.read_bytes())==expected_digest,
        "original Marko Plus 0.4.17 archive mismatch: "+rel)
    req(live.is_file() and live.read_bytes().endswith(archived.read_bytes()),
        "authentic original Marko Plus 0.4.17 history not exact suffix: "+rel)
# x11.0 entry and every intervening pre-0.4.17 entry remain exactly as issued.
for rel, previous_hash, boundary in (
    ("CHANGELOG.md", "461db47a2fe67be429b78438b93093826774e08d6da01eb4f3679602382dba78", b"## 0.4.17 \xe2\x80\x94 Toggle Comment"),
    ("RELEASE_NOTES.md", "c876b49136b7d796360d2fbf25300d6d916cba378bec452d732dafbd21bec5a2", b"# Marko Plus 0.4.17"),
):
    data=(R/"docs"/rel).read_bytes()
    marker=b"# MaqaronyDesk 1.0.0-x11.0"
    pos=data.find(marker)
    req(pos>=0, "original x11.0 release section missing: "+rel)
    if pos>=0:
        prev=data[pos:data.index(boundary,pos)]
        req(sha(prev)==previous_hash, "previous x11.0 and x10 history modified: "+rel)
identity=json.loads((ROOT/'suite-pythoine-component.json').read_text())
req(identity.get('id')=='maqaronydesk' and identity.get('name')=='MaqaronyDesk','Suite product identity')
req(identity.get('icon')=='maqarony_desk/assets/icons/maqaronydesk.png' and (ROOT/identity.get('icon','')).is_file(),'Suite icon missing')
req(identity.get('component_kind')=='extension' and identity.get('capabilities')=={'routing':False,'open':False,'create':False},'Suite extension behavior changed')
req(identity.get('repository')=='https://github.com/brunonlinespace/maqaronydesk','Suite repository')
project=json.loads((R/'maqaronydesk.json').read_text())
req(project.get('id')=='maqaronydesk' and project.get('version')=='1.0.0-x11.1','project manifest')
init=(R/'__init__.py').read_text()
req('APP_NAME = "MaqaronyDesk"' in init and 'APP_ID = "maqaronydesk"' in init and 'APP_VERSION = "1.0.0-x11.1"' in init,'package identity')
app=(R/'app.py').read_text()
req('app.setApplicationName(APP_DISPLAY_NAME)' in app and 'app.setDesktopFileName(APP_RUNTIME_DESKTOP_ID)' in app,'Qt/Plasma desktop identity')
runtime=(R/'services/runtime_paths.py').read_text()
req('QStandardPaths.StandardLocation.AppConfigLocation' in runtime,'platform-aware Qt config location lost')
req('"maqaronydesk.json"' in runtime,'new config namespace missing')
req('"mepynamu.json"' not in runtime,'legacy configuration migrated unexpectedly')
req('".mepynamu-ignore"' in (R/'services/module_scanner.py').read_text(),'pre-existing workspace ignore handling changed')
desktop=(R/'packaging/appimage/maqaronydesk.desktop').read_text()
for line in ('Name=MaqaronyDesk','Exec=maqaronydesk %f','Icon=maqaronydesk','StartupWMClass=MaqaronyDesk'):
    req(line in desktop,'desktop metadata: '+line)
appstream=(R/'packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml').read_text()
for part in ('io.github.brunonlinespace.maqaronydesk','<binary>maqaronydesk</binary>','maqaronydesk.desktop','version="1.0.0-x11.1"','historical attribution'):
    req(part in appstream,'AppStream current release: '+part)
builder=(R/'packaging/fedora/build-appimage.sh').read_text()
for part in ('APP_ID="maqaronydesk"','APP_VERSION="1.0.0-x11.1"','usr/lib/maqaronydesk','PYI_DIST/maqaronydesk/maqaronydesk','ln -s ../lib/maqaronydesk/maqaronydesk','assets/icons/maqaronydesk.png'):
    req(part in builder,'builder package path: '+part)
run=(R/'packaging/appimage/AppRun').read_text()
req('usr/lib/maqaronydesk' in run and '$BUNDLE/maqaronydesk' in run,'AppRun executable path')
req(not (R/'mwpyn').exists(), 'Mwpyn scope violation')

for rel in ('docs/BUILDING.md', 'packaging/README.md'):
    current=(R/rel).read_text()
    req('MaqaronyDesk-1.0.0-x11.1-x86_64.AppImage' in current, 'current build example missing: '+rel)
    for stale in ('Marko-Plus-0.0.9', 'MaqaronyDesk-1.0.0-x1.0', 'MaqaronyDesk-1.0.0-x8.0'):
        req(stale not in current, 'stale build example: '+rel+' '+stale)
req('It combines MaqaronyPad source editing' in appstream and
    'It combines MepySivu source editing' not in appstream, 'current AppStream Pad branding incorrect')
for helper in sorted((R/'packaging').rglob('*.sh')):
    req(helper.stat().st_mode & 0o111 != 0, 'non-executable Fedora script: '+str(helper.relative_to(R)))
if errors:
    print('x11.1 identity/preservation FAILED:')
    for e in errors:print('-',e)
    sys.exit(1)
print('PASS: x11.1 full identity; source AST match; historic source/QA fingerprints; 244 ribbon/icon assets; config isolation and packaging paths')
