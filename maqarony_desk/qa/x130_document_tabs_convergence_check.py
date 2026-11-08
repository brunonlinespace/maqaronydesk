#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.0: exact x12.1 preservation and 25-method Document Tabs extraction.

The issued x12.1 fingerprints are immutable. Earlier release gates are
historical evidence; they are not rewritten to validate new source paths.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
ref = json.loads((P / "qa/x130-preservation-reference.json").read_text())
baseline = ref["baseline_sha256_by_path"]
OLD_VERSION = "1.0.0-x12.1"
VERSION = "1.0.0-x13.0"
errors: list[str] = []

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def check(ok: bool, error: str) -> None:
    if not ok:
        errors.append(error)

# The only changes to existing source: MainWindow inheritance/import/extraction,
# active gate, release identity, appstream current entry, append-only docs, manifest.
metadata = {
    "README.md", "suite-pythoine-component.json",
    "maqarony_desk/__init__.py", "maqarony_desk/app_constants.py",
    "maqarony_desk/maqaronydesk.json", "maqarony_desk/packaging/README.md",
    "maqarony_desk/packaging/fedora/build-appimage.sh",
    "maqarony_desk/packaging/fedora/test-appimage.sh",
    "maqarony_desk/packaging/appimage/maqaronydesk.desktop",
    "maqarony_desk/docs/BUILDING.md", "maqarony_desk/docs/README.md",
}
history = {f"maqarony_desk/docs/{x}" for x in
           ("CHANGELOG.md", "RELEASE_NOTES.md", "RELEASE_CHECKLIST.md")}
arch = "maqarony_desk/docs/ARCHITECTURE.md"
main_rel = "maqarony_desk/widgets/main_window.py"
new_rel = "maqarony_desk/widgets/window_parts/document_tabs.py"
parts = "maqarony_desk/widgets/window_parts/__init__.py"
gate = "maqarony_desk/qa/release_check.py"
manifest = "maqarony_desk/SOURCE_MANIFEST.sha256"
appstream = "maqarony_desk/packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml"
new = {parts, new_rel, "maqarony_desk/qa/x130-preservation-reference.json",
       "maqarony_desk/qa/x130_document_tabs_convergence_check.py"}

check(ref["baseline_version"] == OLD_VERSION, "wrong frozen predecessor")
check(ref["baseline_main_window_sha256"] == baseline[main_rel], "MainWindow baseline mismatch")
for rel, oldsha in baseline.items():
    path = R / rel
    check(path.is_file(), "missing issued-source file: " + rel)
    if not path.is_file():
        continue
    if rel in (metadata | history | {arch, main_rel, gate, manifest, appstream}):
        continue
    check(digest(path.read_bytes()) == oldsha, "pre-existing source/historical record altered: " + rel)

actual = {f.relative_to(R).as_posix() for f in R.rglob("*")
          if f.is_file() and "__pycache__" not in f.parts and f.suffix not in {".pyc", ".pyo"}}
expected = set(baseline) | new
check(actual == expected, f"source inventory drift: added={sorted(actual-expected)[:8]}, removed={sorted(expected-actual)[:8]}")
check((R / parts).read_text() == '"""MaqaronyDesk MainWindow responsibility mixins."""\n',
      "window_parts package initialiser changed")

for rel in metadata:
    content = (R / rel).read_text()
    check(VERSION in content, "current identity absent: " + rel)
    check(digest(content.replace(VERSION, OLD_VERSION).encode()) == baseline[rel],
          "non-identity metadata modified: " + rel)

for rel in history:
    content = (R / rel).read_bytes()
    size = ref["historical_document_lengths"][rel]
    check(content.startswith(("# MaqaronyDesk " + VERSION).encode()),
          "current history header absent: " + rel)
    check(size > 0 and digest(content[-size:]) == baseline[rel],
          "historical release text rewritten: " + rel)
archbytes = (R / arch).read_bytes()
size = ref["architecture_prefix_length"]
check(digest(archbytes[:size]) == baseline[arch], "historical architecture text rewritten")

# Source text is reconstructable byte for byte from the extracted mixin.
window = (R / main_rel).read_text()
mixin = (R / new_rel).read_text()
marker = 'class DocumentTabsMixin:\n'
check(mixin.count(marker) == 1, "DocumentTabsMixin missing or duplicate")
if marker in mixin:
    block = mixin.split(marker, 1)[1].removesuffix('\n')
    restored = window.replace(
        'from maqarony_desk.widgets.window_parts.document_tabs import DocumentTabsMixin\n', '')
    restored = restored.replace(
        'class MainWindow(DocumentTabsMixin, EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):',
        'class MainWindow(EditorCommandsAppearanceMixin, EditorPrintingMixin, QMainWindow):')
    restored = restored.replace(
        'self.shell_ribbon.set_collapsed(True, emit=False)\n\n\n    @staticmethod\n    def _widget_is_within',
        'self.shell_ribbon.set_collapsed(True, emit=False)\n\n' + block +
        '\n    @staticmethod\n    def _widget_is_within')
    check(digest(restored.encode()) == baseline[main_rel],
          "MainWindow cannot reconstruct exact x12.1 file from extracted methods")

m = ast.parse(mixin)
w = ast.parse(window)
mixin_class = next((n for n in m.body if isinstance(n, ast.ClassDef) and n.name == "DocumentTabsMixin"), None)
main_class = next((n for n in w.body if isinstance(n, ast.ClassDef) and n.name == "MainWindow"), None)
if mixin_class is not None and main_class is not None:
    extracted = [n.name for n in mixin_class.body if isinstance(n, ast.FunctionDef)]
    still = {n.name for n in main_class.body if isinstance(n, ast.FunctionDef)}
    check(extracted == ref["extracted_method_names"] and len(extracted) == 25,
          "25 extracted methods have changed or been reordered")
    check(not (set(extracted) & still), "MainWindow retains duplicate extracted methods")
    check(isinstance(main_class.bases[0], ast.Name) and main_class.bases[0].id == "DocumentTabsMixin",
          "MainWindow mixin precedence changed")
    check('marko-plus://navigation/' in mixin and '_NAV_DASHBOARD_TOKEN' in mixin,
          "historical navigation-tab tokens changed")
    check('def _connect_signals(' in window and 'self.document_tabs = QTabBar(' in window,
          "tab widget construction/signal ownership removed from MainWindow")
    check('def _navigate_back(' in window and 'def _toggle_collapsed_mode(' in window
          and 'def _show_quick_tour(' in window,
          "later Stage 3 scopes were accidentally extracted")
else:
    errors.append("MainWindow or DocumentTabsMixin class not found")

check((R / appstream).read_text().count('<release version="' + VERSION + '"') == 1,
      "AppStream current edition metadata missing")
# The x12.1 entry must not be rewritten or removed: record archival continuity.
check('<release version="' + OLD_VERSION + '"' not in (R / appstream).read_text(),
      "AppStream is current-only but still has predecessor as current release")
# Current release test invokes this gate, while the old x12.1 gate remains a historical file.
active = (R / gate).read_text()
check('x130_document_tabs_convergence_check.py' in active,
      "current release checker does not run x13.0 preservation gate")
check(digest((P / 'qa/x121_workspace_dialog_convergence_check.py').read_bytes()) ==
      baseline['maqarony_desk/qa/x121_workspace_dialog_convergence_check.py'],
      "historical x12.1 QA rewritten")
if errors:
    print("FAIL x13.0 preservation/document tabs extraction:")
    for error in errors: print("-", error)
    raise SystemExit(1)
print("PASS x13.0: 25 exact tab methods moved; frozen x12.1 history/production source preserved")
