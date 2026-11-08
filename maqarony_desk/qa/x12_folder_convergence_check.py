#!/usr/bin/env python3
"""MaqaronyDesk x12.0 Stage 1 relocation and exact predecessor preservation gate.

The x11.1 predecessor test and all pre-x12 fixtures remain immutable historical
source. This gate remaps only the six approved paths and the revised import
statements before comparing the *entire* non-tools production AST inventory
with the frozen predecessor-lineage reference. It does not regenerate hashes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
F = json.loads((P / "qa/x11-preservation-reference.json").read_text())
VERSION = "1.0.0-x12.0"
MOVED = {"widgets/mwpyn/" + name: "widgets/" + name for name in ('editor_formatting.py', 'editor_insertion.py', 'editor_preview.py', 'editor_search_view.py', 'editor_source.py', 'editor_widgets.py')}
SOURCE_HASHES = {'editor_formatting.py': '2b910071810097c1eaead8be177eb9a6603ea3305acd90b409ab1253bad7e90a', 'editor_insertion.py': '2a3cc8c14611732f7fa63cf6fe06a7c949eedb8338b44e5f9ad5d3c67b3c1c3d', 'editor_preview.py': 'b0b414eca1cd599ce4969f91130ca5c233541c7a675e382597b9b2dbcfe86d39', 'editor_search_view.py': 'a8db2e7a1c3027da2908951d79e5e1627f7b690d5c8410e1a908883d59c5b250', 'editor_source.py': 'd29be90f6252a00e4a67ab8995022e556aafc0d0f411942141dbbcaff355096e', 'editor_widgets.py': 'df8813b44df453d9cbe00b4b3aed8ed03095eaec3370e55af9a26df4b60561a7'}
HISTORICAL_X111_SHA256 = '3a862572d96a17da9a7829e436281ed2b80783fca97ee7f3ecb9114cf3b2014b'
ORIGINAL_ARCHITECTURE_LENGTH = 3563
errors: list[str] = []


def check(test: bool, message: str) -> None:
    if not test:
        errors.append(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prior_imports(source: str) -> str:
    # Reverse precisely the approved x12 relocation for comparison to x11.1.
    for name in SOURCE_HASHES:
        source = source.replace(
            "maqarony_desk.widgets.mwpyn." + name.removesuffix(".py"),
            "maqarony_desk.widgets." + name.removesuffix(".py"),
        )
    return source


def previous_lineage(source: str) -> str:
    source = prior_imports(source)
    source = source.replace(
        "app.setApplicationName(APP_DISPLAY_NAME)",
        "app.setApplicationName(APP_INTERNAL_NAME)",
    )
    for old, previous in (
        ("maqaronydesk-about.png", "markopad-about.png"),
        ("maqaronydesk-master.png", "markopad-master.png"),
        ("maqaronydesk.ico", "markopad.ico"),
        ("maqaronydesk.png", "markopad.png"),
        ("MaqaronyDesk", "MepyNamu"),
        ("MaqaronyPad", "MepySivu"),
        ("MAQARONYDESK", "MEPYNAMU"),
        ("maqaronydesk", "mepynamu"),
        ("maqarony_desk", "mepynamu"),
        (VERSION, "1.0.0-x10.0"),
    ):
        source = source.replace(old, previous)
    return source

# Six modules really moved: no aliases, no copies, no overwritten method bodies.
package = P / "widgets/mwpyn"
check(package.is_dir() and (package / "__init__.py").is_file(), "missing embedded editor package")
check((package / "__init__.py").read_text().strip() ==
      '"""MaqaronyDesk embedded Markdown editor components (MaqaronyPad lineage)."""',
      "unexpected embedded package initialization code")
for filename, digest in SOURCE_HASHES.items():
    moved = package / filename
    check(moved.is_file(), "missing moved module: " + filename)
    check(not (P / "widgets" / filename).exists(), "old flat module still present: " + filename)
    if moved.is_file():
        check(sha(prior_imports(moved.read_text()).encode()) == digest,
              "moved editor module changed beyond approved imports: " + filename)

# Frozen production source AST identities: map exactly the six relocated paths.
actual: set[str] = set()
for file in P.rglob("*.py"):
    rel = file.relative_to(P).as_posix()
    if rel.startswith("qa/") or rel == "widgets/mwpyn/__init__.py":
        continue
    canonical = MOVED.get(rel, rel)
    actual.add(canonical)
    try:
        current = previous_lineage(file.read_text())
        digest = sha(ast.dump(ast.parse(current), include_attributes=False).encode())
        check(digest == F["production_ast"].get(canonical),
              "production AST / imports changed: " + rel)
    except (OSError, UnicodeError, SyntaxError) as exc:
        errors.append(f"source parse error: {rel}: {exc}")
check(actual == set(F["production_ast"]), "production Python inventory drift outside six moves")

# Exact pre-x12 history and artwork remain protected; current docs are appended.
for key in ("ribbon_sha256", "historical_sha256", "artwork_sha256"):
    for rel, digest in F[key].items():
        if rel in ("docs/CHANGELOG.md", "docs/RELEASE_NOTES.md", "docs/ARCHITECTURE.md"):
            continue
        f = P / rel
        check(f.is_file() and sha(f.read_bytes()) == digest, "archived/asset file modified: " + rel)
arch = (P / "docs/ARCHITECTURE.md").read_bytes()
check(sha(arch[:ORIGINAL_ARCHITECTURE_LENGTH]) == F["historical_sha256"]["docs/ARCHITECTURE.md"],
      "original architecture documentation rewritten")
check(sha((P / "qa/x111_history_and_identity_check.py").read_bytes()) == HISTORICAL_X111_SHA256,
      "x11.1 historical preservation gate modified")
for rel, digest in F["historical_prefix_sha256"].items():
    original = P / "docs/history" / ("MepyNamu-1.0.0-x10.0-" + rel.rsplit("/", 1)[1])
    check(original.is_file() and sha(original.read_bytes()) == digest,
          "original x10 release history modified: " + rel)
for rel, digest in (
    ("CHANGELOG.md", "fda1fd314832022492663cd2d8110e592e54f97cdbfd031b57a88f751b0f9d03"),
    ("RELEASE_NOTES.md", "4b0a5ff11b33d005ff83b92bffc0f19d428cd4804e5df4073120e8b963cfe5e7"),
):
    archived = P / "docs/history" / ("Marko-Plus-0.4.17-" + rel)
    live = P / "docs" / rel
    check(archived.is_file() and sha(archived.read_bytes()) == digest,
          "original Marko Plus 0.4.17 archive modified: " + rel)
    check(live.read_bytes().endswith(archived.read_bytes()),
          "original Marko Plus 0.4.17 suffix modified: " + rel)

# Suite and desktop identity and packaging invariants are inherited from x11.1.
suite = json.loads((R / "suite-pythoine-component.json").read_text())
project = json.loads((P / "maqaronydesk.json").read_text())
check(suite.get("id") == "maqaronydesk" and suite.get("version") == VERSION, "Suite identity/version")
check(suite.get("component_kind") == "extension" and suite.get("capabilities") ==
      {"routing": False, "open": False, "create": False}, "Suite capability changed")
check(suite.get("icon") == "maqarony_desk/assets/icons/maqaronydesk.png" and
      (R / suite.get("icon", "")).is_file(), "Suite icon missing")
check(suite.get("repository") == "https://github.com/brunonlinespace/maqaronydesk", "Suite repository changed")
check(project.get("name") == "MaqaronyDesk" and project.get("id") == "maqaronydesk"
      and project.get("version") == VERSION, "package project identity")
init = (P / "__init__.py").read_text()
check('APP_NAME = "MaqaronyDesk"' in init and 'APP_ID = "maqaronydesk"' in init
      and f'APP_VERSION = "{VERSION}"' in init, "package version")
app = (P / "app.py").read_text()
check("app.setApplicationName(APP_DISPLAY_NAME)" in app and
      "app.setDesktopFileName(APP_RUNTIME_DESKTOP_ID)" in app, "Qt application identity")
runtime = (P / "services/runtime_paths.py").read_text()
check("QStandardPaths.StandardLocation.AppConfigLocation" in runtime and
      '"maqaronydesk.json"' in runtime and '"mepynamu.json"' not in runtime,
      "Qt configuration namespace changed")
check('".mepynamu-ignore"' in (P / "services/module_scanner.py").read_text(),
      "legacy ignore policy changed")
desktop = (P / "packaging/appimage/maqaronydesk.desktop").read_text()
for value in ("Name=MaqaronyDesk", "Exec=maqaronydesk %f", "Icon=maqaronydesk",
              "StartupWMClass=MaqaronyDesk", f"X-AppImage-Version={VERSION}"):
    check(value in desktop, "desktop identity: " + value)
meta = (P / "packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml").read_text()
for value in ("io.github.brunonlinespace.maqaronydesk", "<binary>maqaronydesk</binary>",
              f'version="{VERSION}"', "Structure-only move of six existing Markdown editor modules",
              "It combines MaqaronyPad source editing"):
    check(value in meta, "AppStream identity/history: " + value)
builder = (P / "packaging/fedora/build-appimage.sh").read_text()
for value in ('APP_ID="maqaronydesk"', f'APP_VERSION="{VERSION}"',
              "usr/lib/maqaronydesk", "PYI_DIST/maqaronydesk/maqaronydesk",
              "ln -s ../lib/maqaronydesk/maqaronydesk", "assets/icons/maqaronydesk.png"):
    check(value in builder, "Fedora packaging invariant: " + value)
launcher = (P / "packaging/appimage/AppRun").read_text()
check("usr/lib/maqaronydesk" in launcher and "$BUNDLE/maqaronydesk" in launcher,
      "AppRun path modified")
spec = (P / "packaging/pyinstaller/maqaronydesk.spec").read_text()
check('collect_submodules("maqarony_desk")' in spec, "new package not covered by PyInstaller")
for rel in ("docs/BUILDING.md", "packaging/README.md"):
    check("MaqaronyDesk-1.0.0-x12.0-x86_64.AppImage" in (P / rel).read_text(),
          "current build example stale: " + rel)
for helper in (P / "packaging").rglob("*.sh"):
    check(bool(helper.stat().st_mode & 0o111), "Fedora script lost executable bit: " + str(helper))

# No obsolete editor module routes anywhere in current production Python code.
for file in P.rglob("*.py"):
    if "qa" in file.relative_to(P).parts:
        continue
    text = file.read_text()
    for name in SOURCE_HASHES:
        check("maqarony_desk.widgets." + name.removesuffix(".py") not in text,
              "stale editor import: " + str(file.relative_to(P)) + " :: " + name)


# Previous release content is an exact suffix, not reconstructed history.
for filename, length, digest in [('CHANGELOG.md', 47101, 'ec560f8b1eb0eb3da3a1c1dd78cfafabb898b203797e63aabd1d4d03de334e04'), ('RELEASE_NOTES.md', 7682, 'a9899849ddb871ae3d02286133563501deceea652d7f7d782fee20e2197d2046')]:
    data = (P / "docs" / filename).read_bytes()
    check(len(data) >= length and sha(data[-length:]) == digest,
          "x11.1 and earlier documented release history modified: " + filename)
check(sha((R / "README.md").read_bytes().replace(VERSION.encode(), b"1.0.0-x11.1"))
      == '8363857b3cca23da8e46ce5b824b5e54556d252bb9ade5328af45e30f27d9a5a', "public README changed beyond version")

if errors:
    print("FAIL x12.0 folder convergence / source preservation:")
    for problem in errors:
        print("-", problem)
    sys.exit(1)
print("PASS x12.0: six exact editor moves, unchanged method bodies, full AST inventory,")
print("    historical x11.1/x10/0.4.17 provenance, app identity and package invariants")
