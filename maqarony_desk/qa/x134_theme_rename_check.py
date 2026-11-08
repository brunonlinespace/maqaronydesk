#!/usr/bin/env python3
"""Current-edition theme rename guard; compare with complete frozen predecessor."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE.parent
REL = PACKAGE.name
REF = json.loads((PACKAGE / "qa/x134-theme-predecessor.json").read_text(encoding="utf-8"))
BASE = REF["previous_sha256_by_path"]
OLD = REF["baseline_version"]
NEW = REF["current_version"]
OLD_PATH = REF["old_theme_path"]
NEW_PATH = REF["new_theme_path"]

errors = []
def require(ok: bool, message: str):
    if not ok: errors.append(message)
def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
def get(rel: str) -> bytes:
    return (SOURCE / rel).read_bytes()

# Freeze the entire immediate predecessor, not just the two palette functions.
additional = {REL+"/qa/x134-theme-predecessor.json", REL+"/qa/x134_theme_rename_check.py"} | set()
actual = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*")
          if p.is_file() and "__pycache__" not in p.parts
          and p.suffix not in {".pyc", ".pyo"}
          and p.relative_to(SOURCE).parts[:2] not in {(REL,"build"),(REL,"dist")}}
expected = (set(BASE) - {OLD_PATH}) | {NEW_PATH} | additional
require(actual == expected, "Inventory changes outside approved rename/additions: "+str(sorted(actual ^ expected)[:12]))
require(REF["old_theme_sha256"] == BASE[OLD_PATH], "Frozen palette reference is inconsistent")
require(NEW_PATH in actual and OLD_PATH not in actual, "Theme file must move exclusively")
if NEW_PATH in actual:
    require(sha(get(NEW_PATH)) == BASE[OLD_PATH], "Theme bytes were modified")
    old_tree = ast.parse((SOURCE/NEW_PATH).read_text(encoding="utf-8"))
    funcs = {node.name for node in old_tree.body if isinstance(node, ast.FunctionDef)}
    require({"apply_theme", "effective_scheme"} <= funcs, "Theme public functions missing")

importers = set(REF["approved_importer_paths"])
current_meta = {'maqarony_desk/maqaronydesk.json', 'suite-pythoine-component.json', 'maqarony_desk/packaging/README.md', 'maqarony_desk/packaging/fedora/test-appimage.sh', 'README.md', 'maqarony_desk/packaging/fedora/build-appimage.sh', 'maqarony_desk/docs/README.md', 'maqarony_desk/docs/BUILDING.md', 'maqarony_desk/__init__.py', 'maqarony_desk/app_constants.py', 'maqarony_desk/packaging/appimage/maqaronydesk.desktop'}
history = {REL+"/docs/RELEASE_NOTES.md", REL+"/docs/CHANGELOG.md"}
architecture = REL+"/docs/ARCHITECTURE.md"
appstream = REL+"/packaging/appimage/io.github.brunonlinespace." + REL.replace("_","") + ".metainfo.xml"
manifest = REL+"/SOURCE_MANIFEST.sha256"
release_gate = REL+"/qa/release_check.py"
allowed = importers | current_meta | history | {architecture, appstream, manifest, release_gate, REL+"/docs/RELEASE_CHECKLIST.md"}
for rel, digest in BASE.items():
    if rel == OLD_PATH: continue
    p = SOURCE/rel
    require(p.is_file(), "Predecessor file missing: "+rel)
    if p.is_file() and rel not in allowed:
        require(sha(p.read_bytes())==digest, "Unapproved change, including historical QA: "+rel)
for rel in importers:
    before = b'maqarony_desk.widgets.markopad_theme'
    after = b'maqarony_desk.widgets.theme'
    actual_bytes = get(rel)
    # Invert exactly one import-location replacement; all other production bytes stay fixed.
    require(actual_bytes.count(after)==1 and before not in actual_bytes, "Theme importer wasn't converted exactly once: "+rel)
    require(sha(actual_bytes.replace(after,before)) == BASE[rel], "Other importer content changed: "+rel)

for rel in current_meta:
    actual_bytes = get(rel)
    reverted=actual_bytes.replace(NEW.encode(), OLD.encode())
    if rel == "README.md" and REL == "riqatony_desk":
        reverted = reverted.replace(b"Current source edition:", b"Current corrective source edition:")
    require(NEW.encode() in actual_bytes, "New release identity missing: "+rel)
    require(sha(reverted) == BASE[rel], "Current metadata changed beyond version/name: "+rel)
for rel in history:
    data=get(rel)
    n=REF["historical_lengths"][rel]
    require(sha(data[-n:])==BASE[rel], "Earlier changelog/release notes overwritten: "+rel)
    require(data.startswith(("# "+'MaqaronyDesk'+" "+NEW).encode()), "New release history entry missing: "+rel)
content=get(architecture)
n=REF["historical_lengths"][architecture]
require(sha(content[:n])==BASE[architecture], "Prior architecture documentation rewritten")

if REL == "maqarony_desk":
    check_rel=REL+"/docs/RELEASE_CHECKLIST.md"
    n=REF["historical_lengths"][check_rel]
    require(sha(get(check_rel)[-n:])==BASE[check_rel], "Earlier release checklist rewritten")
else:
    checklist=REL+"/docs/RELEASE_CHECKLIST-x13.5.md"
    require(checklist in actual, "Current release checklist missing")
    require(sha(get(REL+"/rich_text_support.py"))==BASE[REL+"/rich_text_support.py"],
            "rich_text_support.py was modified against explicit instructions")

app=get(appstream).decode("utf-8")
require(app.count('<release version="'+NEW+'"')==1, "AppStream must have exactly current release")
require('<release version="'+OLD+'"' not in app,"AppStream contains predecessor as current feed")
require(app.count("<release version=")==1,"AppStream must retain single current release entry")
checker=get(release_gate).decode("utf-8")
require("x134_theme_rename_check.py" in checker,"Current release gate does not run theme preservation")
require("theme.py" in checker if REL=="riqatony_desk" else True,"Riqatony gate still uses old palette location")
require(OLD_PATH not in {f.relative_to(SOURCE).as_posix() for f in PACKAGE.rglob('*.py') if f.is_file() and 'widgets' in f.parts}, "Old theme file still exists")

if errors:
    for error in errors: print("FAIL "+NEW+": "+error)
    raise SystemExit(1)
print("PASS "+NEW+": byte-identical theme relocation, imports, full predecessor and history integrity")
