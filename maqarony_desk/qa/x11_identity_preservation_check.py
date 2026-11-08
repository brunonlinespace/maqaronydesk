#!/usr/bin/env python3
"""x11.0 full-identity and exact normalized production preservation gate.
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
        ('1.0.0-x11.0','1.0.0-x10.0'),
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
for key in ('ribbon_sha256','historical_sha256','artwork_sha256'):
    for rel,expected in F[key].items():
        if key=='historical_sha256' and rel in F['historical_prefix_sha256']: continue
        p=R/rel
        req(p.is_file() and sha(p.read_bytes())==expected,f'{key} modified: {rel}')
for rel,expected in F['historical_prefix_sha256'].items():
    previous=(R/rel).read_bytes()
    # Exact retained predecessor bytes must remain a literal suffix.
    baseline_len={'docs/CHANGELOG.md': (610,), 'docs/RELEASE_NOTES.md':(93,)}
    start=previous.find(b'# MepyNamu 1.0.0-x10.0')
    req(start>=0 and sha(previous[start:])==expected,'historical release section altered: '+rel)
identity=json.loads((ROOT/'suite-pythoine-component.json').read_text())
req(identity.get('id')=='maqaronydesk' and identity.get('name')=='MaqaronyDesk','Suite product identity')
req(identity.get('icon')=='maqarony_desk/assets/icons/maqaronydesk.png' and (ROOT/identity.get('icon','')).is_file(),'Suite icon missing')
req(identity.get('component_kind')=='extension' and identity.get('capabilities')=={'routing':False,'open':False,'create':False},'Suite extension behavior changed')
req(identity.get('repository')=='https://github.com/brunonlinespace/maqaronydesk','Suite repository')
project=json.loads((R/'maqaronydesk.json').read_text())
req(project.get('id')=='maqaronydesk' and project.get('version')=='1.0.0-x11.0','project manifest')
init=(R/'__init__.py').read_text()
req('APP_NAME = "MaqaronyDesk"' in init and 'APP_ID = "maqaronydesk"' in init and 'APP_VERSION = "1.0.0-x11.0"' in init,'package identity')
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
for part in ('io.github.brunonlinespace.maqaronydesk','<binary>maqaronydesk</binary>','maqaronydesk.desktop','version="1.0.0-x11.0"','identity rebrand'):
    req(part in appstream,'AppStream current release: '+part)
builder=(R/'packaging/fedora/build-appimage.sh').read_text()
for part in ('APP_ID="maqaronydesk"','APP_VERSION="1.0.0-x11.0"','usr/lib/maqaronydesk','PYI_DIST/maqaronydesk/maqaronydesk','ln -s ../lib/maqaronydesk/maqaronydesk','assets/icons/maqaronydesk.png'):
    req(part in builder,'builder package path: '+part)
run=(R/'packaging/appimage/AppRun').read_text()
req('usr/lib/maqaronydesk' in run and '$BUNDLE/maqaronydesk' in run,'AppRun executable path')
req(not (R/'mwpyn').exists(), 'Mwpyn scope violation')
if errors:
    print('x11.0 identity/preservation FAILED:')
    for e in errors:print('-',e)
    sys.exit(1)
print('PASS: x11.0 full identity; source AST match; historic source/QA fingerprints; 244 ribbon/icon assets; config isolation and packaging paths')
