#!/usr/bin/env python3
"""MaqaronyDesk x12.1: frozen x12.0 source comparison; no historical rewrites.

The reference contains SHA-256 fingerprints of the *issued x12.0 source*,
including every old QA script and historic record. It is not regenerated when
checking the x12.1 release.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
BASELINE = json.loads((P / "qa/x121-preservation-reference.json").read_text())
SOURCE = BASELINE["baseline_sha256_by_path"]
VERSION = "1.0.0-x12.1"
PREVIOUS = "1.0.0-x12.0"
WORKSPACE = ("navigation", "dashboard", "dashboard_card", "folder_dashboard")
DIALOGS = ("about_dialog", "closing_dialog", "first_run_dialog", "projects_dialog",
           "resolve_open_documents_dialog", "shortcuts_dialog")
MOVED = {f"maqarony_desk/widgets/{n}.py": f"maqarony_desk/widgets/workspace/{n}.py" for n in WORKSPACE}
MOVED.update({f"maqarony_desk/widgets/{n}.py": f"maqarony_desk/widgets/dialogs/{n}.py" for n in DIALOGS})
RELEASE_METADATA = {
    "README.md", "suite-pythoine-component.json", "maqarony_desk/__init__.py",
    "maqarony_desk/app_constants.py", "maqarony_desk/maqaronydesk.json",
    "maqarony_desk/packaging/appimage/maqaronydesk.desktop",
    "maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml",
    "maqarony_desk/packaging/fedora/build-appimage.sh",
    "maqarony_desk/packaging/fedora/test-appimage.sh",
    "maqarony_desk/docs/BUILDING.md", "maqarony_desk/packaging/README.md",
    "maqarony_desk/docs/README.md",
}
HISTORY = {"maqarony_desk/docs/CHANGELOG.md", "maqarony_desk/docs/RELEASE_NOTES.md",
           "maqarony_desk/docs/RELEASE_CHECKLIST.md"}
APPEND_ONLY = "maqarony_desk/docs/ARCHITECTURE.md"
ACTIVE_RELEASE_GATE = "maqarony_desk/qa/release_check.py"
MANIFEST = "maqarony_desk/SOURCE_MANIFEST.sha256"
NEW = {
    "maqarony_desk/widgets/workspace/__init__.py",
    "maqarony_desk/widgets/dialogs/__init__.py",
    "maqarony_desk/qa/x121-preservation-reference.json",
    "maqarony_desk/qa/x121_workspace_dialog_convergence_check.py",
    "maqarony_desk/qa/x121_direct_drop_check.py",
}
errors: list[str] = []

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def check(condition: bool, message: str) -> None:
    if not condition: errors.append(message)

def reverse_moves(content: str, rel: str) -> str:
    # Exactly reverse approved import routes. No method-body transformations.
    for n in WORKSPACE:
        content = content.replace("maqarony_desk.widgets.workspace." + n,
                                  "maqarony_desk.widgets." + n)
    for n in DIALOGS:
        content = content.replace("maqarony_desk.widgets.dialogs." + n,
                                  "maqarony_desk.widgets." + n)
    if rel == "maqarony_desk/widgets/__init__.py":
        content = content.replace("from .workspace.navigation import NavigationWidget",
                                  "from .navigation import NavigationWidget")
    if rel in {f"maqarony_desk/widgets/{n}.py" for n in ("dashboard", "dashboard_card", "folder_dashboard")}:
        content = content.replace('Path(__file__).resolve().parents[2] / "assets"',
                                  'Path(__file__).resolve().parent.parent / "assets"')
    return content

# Protect all preexisting files, including old validators and archived records.
for oldpath, digest in SOURCE.items():
    newpath = MOVED.get(oldpath, oldpath)
    f = R / newpath
    check(f.is_file(), "baseline file missing: " + newpath)
    if not f.is_file(): continue
    if oldpath in (RELEASE_METADATA | HISTORY | {APPEND_ONLY, ACTIVE_RELEASE_GATE, MANIFEST}):
        continue
    if oldpath.endswith('.py') and (oldpath != newpath or '/qa/' not in oldpath):
        # Import routing is the only code change except version constants.
        prior = reverse_moves(f.read_text(), oldpath)
        check(sha(prior.encode()) == digest, "protected source changed beyond imports/assets: " + oldpath)
    else:
        check(sha(f.read_bytes()) == digest, "historical or untouched file rewritten: " + oldpath)

# Prior release notes and changelogs must remain exact suffixes of the new files.
for rel in HISTORY:
    f = R / rel
    data = f.read_bytes() if f.is_file() else b''
    check(len(data) > 150 and data.startswith(("# MaqaronyDesk " + VERSION).encode()),
          "new release note missing: " + rel)
    # A cryptographically frozen full baseline suffix, not a reconstructed note.
    old_suffix_len = BASELINE.get("historical_document_lengths", {}).get(rel)
    if old_suffix_len is not None:
        check(sha(data[-old_suffix_len:]) == SOURCE[rel], "historical release record rewritten: " + rel)
    else:
        errors.append("missing historical document length fingerprint: " + rel)
arch = (R / APPEND_ONLY).read_bytes()
length = BASELINE.get("architecture_prefix_length")
check(length is not None and sha(arch[:length]) == SOURCE[APPEND_ONLY],
      "historical architecture text rewritten")

# The only added module locations and absence of all ten old paths.
for old, new in MOVED.items():
    check(not (R / old).exists() and (R / new).is_file(), "move not exclusive: " + old)
for rel, value in (("workspace", '"""MaqaronyDesk workspace navigation and dashboard widgets."""\n'),
                   ("dialogs", '"""MaqaronyDesk application dialogs."""\n')):
    f = P / "widgets" / rel / "__init__.py"
    check(f.is_file() and f.read_text() == value, "unexpected new package initializer: " + rel)

# Old direct-drop QA is an immutable historical test. The current-path adapter
# must contain exactly the old assertions with only two source filenames changed.
original = (P / "qa/direct_drop_check.py").read_text()
new_direct_drop = (P / "qa/x121_direct_drop_check.py").read_text()
check(sha(original.encode()) == SOURCE["maqarony_desk/qa/direct_drop_check.py"],
      "historical direct-drop QA changed")
check(new_direct_drop.replace("widgets/workspace/navigation.py", "widgets/navigation.py")
      .replace("widgets/workspace/folder_dashboard.py", "widgets/folder_dashboard.py") == original,
      "new direct-drop QA changed assertions beyond approved paths")

# Complete source inventory excludes no additional or undeclared files.
actual = {f.relative_to(R).as_posix() for f in R.rglob('*')
          if f.is_file() and '__pycache__' not in f.parts and f.suffix not in {'.pyc', '.pyo'}}
expected = (set(SOURCE) - set(MOVED)) | set(MOVED.values()) | NEW
check(actual == expected, f"source inventory drift: added={sorted(actual-expected)[:8]}, removed={sorted(expected-actual)[:8]}")

# Current release identity changes are tightly scoped, and include no old version as the current label.
for rel in RELEASE_METADATA - {"maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml"}:
    f = R / rel
    if not f.exists(): continue
    s = f.read_text()
    check(VERSION in s, "stale current release identity in " + rel)
    if rel != "maqarony_desk/docs/README.md":
        # Current-only files: strictly version-only difference from baseline verified via prior payload SHA.
        check(sha(s.replace(VERSION, PREVIOUS).encode()) == SOURCE[rel],
              "unapproved metadata edit: " + rel)

# Validate all module imports and three modified resource paths directly.
for f in P.rglob('*.py'):
    if 'qa' in f.relative_to(P).parts: continue
    t = f.read_text()
    for n in WORKSPACE + DIALOGS:
        check('maqarony_desk.widgets.' + n not in t,
              "stale flat module import: " + str(f.relative_to(P)) + " => " + n)
for n in ("dashboard", "dashboard_card", "folder_dashboard"):
    t = (P / "widgets/workspace" / (n + ".py")).read_text()
    check(t.count('Path(__file__).resolve().parents[2] / "assets"') == 1,
          "icon path not anchored to original package asset root: " + n)

# Unmodified x12 preservation test remains a historical record and is never retargeted.
check("maqarony_desk/qa/x12_folder_convergence_check.py" in SOURCE,
      "x12.0 baseline gate absent")

if errors:
    print("FAIL MaqaronyDesk x12.1 exact-source preservation:")
    for error in errors: print("-", error)
    raise SystemExit(1)
print("PASS x12.1: 10 exclusive module relocations, exact baseline source preservation,")
print("    archived release history, resource anchors, package inventory and imports")
