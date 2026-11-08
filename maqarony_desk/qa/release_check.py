#!/usr/bin/env python3
# MaqaronyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Static release checks that do not require PyQt6 or a display server."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT.parent
ROOT = SOURCE_ROOT
EXPECTED_VERSION = "1.0.0"

# Generated build environments must never be treated as release source.
# Python caches in the working tree are ordinary local artifacts and are
# ignored by Git. They only become a release error when Git reports that they
# are actually tracked.
GENERATED_ROOT_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "ENV",
    "build",
    "dist",
    "dist-appimage",
    "AppDir",
    "MaqaronyDesk.AppDir",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "my library",
}


def relative_parts(path: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(ROOT).parts
    except ValueError:
        return path.parts


def is_generated_area(path: Path) -> bool:
    return any(part in GENERATED_ROOT_NAMES for part in relative_parts(path))


def is_python_cache_path(path: Path) -> bool:
    parts = relative_parts(path)
    return "__pycache__" in parts or path.suffix in {".pyc", ".pyo"}


def tracked_python_cache_files() -> list[Path]:
    """Return cache files tracked by Git, or an empty list outside a checkout."""
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=False,
            capture_output=True,
        )
    except OSError:
        return []

    if result.returncode != 0:
        return []

    tracked: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = Path(raw.decode("utf-8"))
        except UnicodeDecodeError:
            continue
        candidate = ROOT / relative
        if is_python_cache_path(candidate):
            tracked.append(relative)
    return sorted(tracked)


def local_python_cache_paths() -> list[Path]:
    """Return non-build cache paths for a helpful, non-failing notice."""
    return sorted(
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if not is_generated_area(path) and is_python_cache_path(path)
    )


def read_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        raise ValueError("not a valid PNG")
    return struct.unpack(">II", data[16:24])



def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_identity() -> dict[str, str]:
    """Read the dependency-free canonical identity from maqarony_desk/__init__.py."""
    source = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        "APP_NAME",
        "APP_ID",
        "APP_VERSION",
        "PUBLISHER_ID",
        "DESKTOP_ID",
    }
    values: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                values[target.id] = node.value.value
    return values


def main() -> int:
    errors: list[str] = []

    root_entries = {
        path.name
        for path in SOURCE_ROOT.iterdir()
        if path.name != "__pycache__"
    }
    if root_entries != {"README.md", "main.py", "suite-pythoine-component.json", "desk-health-check.json", "maqarony_desk"}:
        errors.append(
            "Source root must contain only README.md, main.py, suite-pythoine-component.json, desk-health-check.json, and maqarony_desk/: "
            f"{sorted(root_entries)}"
        )

    for source in sorted(ROOT.rglob("*.py")):
        if is_generated_area(source) or "__pycache__" in relative_parts(source):
            continue
        try:
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f"{source.relative_to(ROOT)}: {exc}")

    required = (
        ".gitignore",
        ".gitattributes",
        "LICENSE",
        "docs/README.md",
        "docs/CHANGELOG.md",
        "docs/CONTRIBUTING.md",
        "docs/SECURITY.md",
        "docs/BUILDING.md",
        "docs/QA.md",
        "docs/ARCHITECTURE.md",
        "docs/PROJECT_MEMORY.md",
        "docs/ROADMAP.md",
        "docs/RELEASE_NOTES.md",
        "docs/RELEASE_CHECKLIST.md",
        "requirements.txt",
        ".mepynamu-ignore.example",
        "maqaronydesk.json",
        "legacy_ricopad.py",
        "SOURCE_MANIFEST.sha256",
        "packaging/appimage/maqaronydesk.desktop",
        "packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml",
        "packaging/fedora/build-appimage.sh",
        "packaging/fedora/install-build-deps.sh",
        "packaging/pyinstaller/build-requirements.txt",
        "packaging/fedora/test-appimage.sh",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/pull_request_template.md",
        "qa/x12_folder_convergence_check.py",
        "qa/x121-preservation-reference.json",
        "qa/x121_workspace_dialog_convergence_check.py",
        "qa/x121_direct_drop_check.py",
        "qa/x130-preservation-reference.json",
        "qa/x130_document_tabs_convergence_check.py",
        "qa/x131-preservation-reference.json",
        "qa/x131_navigation_history_convergence_check.py",
        "qa/x131_navigation_history_headless_check.py",
        "widgets/window_parts/navigation_history.py",
        "qa/x132-preservation-reference.json",
        "qa/x132_layout_controls_convergence_check.py",
        "qa/x132_layout_controls_headless_check.py",
        "widgets/window_parts/layout_controls.py",
        "qa/x133-preservation-reference.json",
        "qa/x133_help_actions_convergence_check.py",
        "qa/x134_theme_rename_check.py",
        "qa/x140_dashboard_palette_qa.py",
        "qa/x140-dashboard-predecessor.json",
        "qa/x150_shutdown_compatibility_qa.py",
        "qa/x151_layout_geometry_qa.py",
        "qa/x153_visibility_batch_qa.py",
        "qa/x162_source_scrolling_qa.py",
        "qa/x170_preview_replace_qa.py",
        "qa/x170-predecessor-code-sha256.json",
        "qa/x171_properties_datetime_qa.py",
        "qa/x171-predecessor-code-sha256.json",
        "qa/x172_newline_convergence_qa.py",
        "qa/x172-predecessor-code-sha256.json",
        "qa/x160-predecessor-fingerprints.json",
        "qa/x152-predecessor-fingerprints.json",
        "qa/x151-predecessor-fingerprints.json",
        "qa/x150-predecessor-fingerprints.json",
        "qa/x134-theme-predecessor.json",
        "qa/x133_help_actions_headless_check.py",
        "widgets/window_parts/help_actions.py",
        "qa/marko_plus_0_0_3_check.py",
        "qa/marko_plus_0_0_5_check.py",
        "qa/marko_plus_0_0_6_check.py",
        "qa/marko_plus_0_0_7_check.py",
        "qa/marko_plus_0_0_8_check.py",
        "qa/marko_plus_0_0_9_check.py",
        "qa/marko_plus_0_1_0_check.py",
        "qa/marko_plus_0_1_1_check.py",
        "qa/marko_plus_0_1_2_check.py",
        "qa/marko_plus_0_1_3_check.py",
        "qa/marko_plus_0_1_4_check.py",
        "qa/marko_plus_0_1_5_check.py",
        "qa/marko_plus_0_1_6_check.py",
        "qa/marko_plus_0_1_7_check.py",
        "qa/marko_plus_0_1_8_check.py",
        "qa/marko_plus_0_1_9_check.py",
        "qa/marko_plus_0_1_10_check.py",
        "qa/marko_plus_0_2_0_check.py",
        "qa/marko_plus_0_2_1_check.py",
        "qa/marko_plus_0_2_2_check.py",
        "qa/marko_plus_0_2_3_check.py",
        "qa/marko_plus_0_2_4_check.py",
        "qa/marko_plus_0_2_5_check.py",
        "qa/marko_plus_0_3_0_check.py",
        "qa/marko_plus_0_3_1_check.py",
        "qa/marko_plus_0_3_2_check.py",
        "qa/marko_plus_0_3_3_check.py",
        "qa/marko_plus_0_3_4_check.py",
        "qa/marko_plus_0_3_5_check.py",
        "qa/marko_plus_0_3_6_check.py",
        "qa/marko_plus_0_3_7_check.py",
        "qa/marko_plus_0_3_8_check.py",
        "qa/marko_plus_0_3_10_check.py",
        "qa/marko_plus_0_4_1_check.py",
        "qa/marko_plus_0_4_2_check.py",
        "qa/marko_plus_0_4_4_check.py",
        "qa/marko_plus_0_4_6_check.py",
        "qa/marko_plus_0_4_7_check.py",
        "qa/marko_plus_0_4_8_check.py",
        "qa/marko_plus_0_4_9_check.py",
        "qa/marko_plus_0_4_10_check.py",
        "qa/marko_plus_0_4_11_check.py",
        "qa/marko_plus_0_4_12_check.py",
        "qa/marko_plus_0_4_13_check.py",
        "qa/marko_plus_0_4_14_check.py",
        "qa/marko_plus_0_4_15_check.py",
        "qa/marko_plus_0_4_17_check.py",
        "widgets/dialogs/resolve_open_documents_dialog.py",
        "widgets/window_parts/__init__.py",
        "widgets/window_parts/document_tabs.py",
        "services/open_document_monitor.py",
        "widgets/shell_ribbon.py",
    )
    for relative in required:
        if not (PACKAGE_ROOT / relative).is_file():
            errors.append(f"Missing required program file: {relative}")

    obsolete_files = (
        ".python-lair-ignore.example",
        "python-lair.json",
        "services/process_manager.py",
        "services/runtime_launcher.py",
        "services/script_runtime.py",
        "qa/runtime_launcher_check.py",
        "qa/terminal_force_stop_check.py",
        "packaging/appimage/python-lair-2.desktop",
        "packaging/appimage/io.github.brunonlinespace.python_lair.metainfo.xml",
        "packaging/pyinstaller/python-lair-2.spec",
    )
    for relative in obsolete_files:
        if (PACKAGE_ROOT / relative).exists():
            errors.append(f"Obsolete inherited file remains: {relative}")

    launcher = (SOURCE_ROOT / "main.py").read_text(encoding="utf-8")
    if "from maqarony_desk.app import main" not in launcher:
        errors.append(
            "Root main.py must be a location-independent maqarony_desk.app launcher"
        )

    expected_package_identity = {
        "APP_NAME": "MaqaronyDesk",
        "APP_ID": "maqaronydesk",
        "APP_VERSION": EXPECTED_VERSION,
        "PUBLISHER_ID": "brunonlinespace",
        "DESKTOP_ID": "maqaronydesk",
    }
    actual_package_identity = package_identity()
    for key, expected in expected_package_identity.items():
        if actual_package_identity.get(key) != expected:
            errors.append(
                f"Package identity mismatch: {key} "
                f"(expected {expected!r}, got {actual_package_identity.get(key)!r})"
            )

    project_manifest = PACKAGE_ROOT / "maqaronydesk.json"
    expected_identity = {
        "name": "MaqaronyDesk",
        "id": "maqaronydesk",
        "version": EXPECTED_VERSION,
        "publisher_id": "brunonlinespace",
        "desktop_id": "maqaronydesk",
        "repository": "https://github.com/brunonlinespace/maqaronydesk",
        "tagline": "Friendly. Fast. Focused.",
    }
    try:
        manifest_identity = json.loads(project_manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"Invalid MaqaronyDesk project manifest: {exc}")
        manifest_identity = {}
    for key, expected in expected_identity.items():
        if manifest_identity.get(key) != expected:
            errors.append(
                f"Project manifest identity mismatch: {key} "
                f"(expected {expected!r}, got {manifest_identity.get(key)!r})"
            )

    package_to_manifest = {
        "APP_NAME": "name",
        "APP_ID": "id",
        "APP_VERSION": "version",
        "PUBLISHER_ID": "publisher_id",
        "DESKTOP_ID": "desktop_id",
    }
    for package_key, manifest_key in package_to_manifest.items():
        if actual_package_identity.get(package_key) != manifest_identity.get(manifest_key):
            errors.append(
                "Package/manifest identity disagreement: "
                f"{package_key} != {manifest_key}"
            )

    component_manifest = SOURCE_ROOT / "suite-pythoine-component.json"
    expected_component = {
        "id": "maqaronydesk",
        "name": "MaqaronyDesk",
        "description": "Managed-workspace Markdown application in the Plus family.",
        "component_kind": "extension",
        "extensions": [],
        "portable_command": ["main.py"],
        "icon": "maqarony_desk/assets/icons/maqaronydesk.png",
        "version": EXPECTED_VERSION,
        "publisher": "brunonlinespace",
        "repository": "https://github.com/brunonlinespace/maqaronydesk",
        "desktop_id": "maqaronydesk",
        "tagline": "Friendly. Fast. Focused.",
        "publisher_id": "brunonlinespace",
        "capabilities": {"routing": False, "open": False, "create": False},
    }
    try:
        component_identity = json.loads(component_manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"Invalid Suite Pythoine component manifest: {exc}")
        component_identity = {}
    for key, expected in expected_component.items():
        if component_identity.get(key) != expected:
            errors.append(
                f"Suite component manifest mismatch: {key} "
                f"(expected {expected!r}, got {component_identity.get(key)!r})"
            )

    # This is the same simple source identity surface Suite can safely probe:
    # it must work without PyQt6 and must print exactly '<name> <version>'.
    expected_probe = f"{expected_identity['name']} {EXPECTED_VERSION}"
    try:
        probe = subprocess.run(
            [sys.executable, str(SOURCE_ROOT / "main.py"), "--version"],
            cwd=SOURCE_ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Portable identity probe could not run: {exc}")
    else:
        if probe.returncode != 0:
            errors.append(
                "Portable identity probe failed: "
                f"exit={probe.returncode}, stderr={probe.stderr.strip()!r}"
            )
        elif probe.stdout.strip() != expected_probe:
            errors.append(
                "Portable identity probe mismatch: "
                f"expected {expected_probe!r}, got {probe.stdout.strip()!r}"
            )

    app_source = (PACKAGE_ROOT / "app.py").read_text(encoding="utf-8")
    app_constants_source = (PACKAGE_ROOT / "app_constants.py").read_text(encoding="utf-8")
    if "APP_RUNTIME_DESKTOP_ID = DESKTOP_ID" not in app_constants_source:
        errors.append("Runtime desktop identity is not tied to canonical DESKTOP_ID")
    if "app.setDesktopFileName(APP_RUNTIME_DESKTOP_ID)" not in app_source:
        errors.append("Qt runtime desktop identity does not use APP_RUNTIME_DESKTOP_ID")
    if "app.setDesktopFileName(DESKTOP_ID)" in app_source:
        errors.append("Qt still sets desktop identity directly from the old DESKTOP_ID call site")

    desktop_text = (PACKAGE_ROOT / "packaging/appimage/maqaronydesk.desktop").read_text(encoding="utf-8")
    for fragment in (
        "StartupWMClass=MaqaronyDesk",
        "Name=MaqaronyDesk",
        "Exec=maqaronydesk %f",
        "MimeType=text/markdown;",
    ):
        if fragment not in desktop_text:
            errors.append(f"Desktop entry identity mismatch: missing {fragment}")
    if desktop_text.count("MimeType=") != 1:
        errors.append("Desktop entry must contain exactly one MIME declaration")
    if "%F" in desktop_text:
        errors.append("Desktop entry must remain single-file %f; %F is forbidden")
    if "text/plain" in desktop_text or "text/x-markdown" in desktop_text:
        errors.append("Desktop entry contains an unsupported Markdown MIME alias")

    metadata_checks = {
        "packaging/appimage/maqaronydesk.desktop": f"X-AppImage-Version={EXPECTED_VERSION}",
        "packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml": f'<release version="{EXPECTED_VERSION}"',
        "packaging/fedora/build-appimage.sh": f'APP_VERSION="{EXPECTED_VERSION}"',
        "docs/RELEASE_CHECKLIST.md": f"MaqaronyDesk {EXPECTED_VERSION}",
    }
    for relative, fragment in metadata_checks.items():
        path = PACKAGE_ROOT / relative
        if path.is_file() and fragment not in path.read_text(encoding="utf-8"):
            errors.append(f"Version metadata mismatch in {relative}: {fragment}")

    appstream_path = PACKAGE_ROOT / "packaging/appimage/io.github.brunonlinespace.maqaronydesk.metainfo.xml"
    if appstream_path.is_file():
        try:
            import xml.etree.ElementTree as ET
            appstream_root = ET.parse(appstream_path).getroot()
            if (appstream_root.findtext("id") or "").strip() != "io.github.brunonlinespace.maqaronydesk":
                errors.append("AppStream ID must remain reverse-DNS metadata identity")
            launchable = appstream_root.find("launchable[@type='desktop-id']")
            if launchable is None or (launchable.text or "").strip() != "maqaronydesk.desktop":
                errors.append("AppStream desktop launchable must be maqaronydesk.desktop")
            developer = appstream_root.find("developer[@id='io.github.brunonlinespace']")
            if developer is None or (developer.findtext("name") or "").strip() != "Bruno Machado":
                errors.append("AppStream structured developer metadata is missing or stale")
            release_nodes = appstream_root.findall("./releases/release")
            if len(release_nodes) != 1 or release_nodes[0].attrib.get("version") != EXPECTED_VERSION:
                errors.append("AppStream releases must contain the current release only")
            if appstream_root.find("content_rating[@type='oars-1.1']") is None:
                errors.append("AppStream OARS 1.1 content rating is missing")
            media_types = {(node.text or "").strip() for node in appstream_root.findall("./provides/mediatype")}
            if media_types != {"text/markdown"}:
                errors.append(f"AppStream must advertise exactly text/markdown, got {sorted(media_types)!r}")
        except (OSError, ET.ParseError) as exc:
            errors.append(f"Invalid AppStream metadata: {exc}")

    build_script = PACKAGE_ROOT / "packaging/fedora/build-appimage.sh"
    if build_script.is_file():
        build_text = build_script.read_text(encoding="utf-8")
        release_check_call = build_text.find("$PROGRAM_ROOT/qa/release_check.py")
        venv_creation = build_text.find('python3 -m venv "$VENV"')
        if release_check_call < 0 or venv_creation < 0:
            errors.append("Fedora build script is missing validation or venv creation")
        elif release_check_call > venv_creation:
            errors.append("Fedora build script creates the venv before source validation")

        for fragment in (
            'APP_NAME="MaqaronyDesk"',
            'APP_ID="maqaronydesk"',
            'OUTPUT_STEM="MaqaronyDesk"',
            'COMPONENT_MANIFEST="$PROJECT_ROOT/suite-pythoine-component.json"',
            'PROJECT_MANIFEST="$PROGRAM_ROOT/maqaronydesk.json"',
            'SOURCE_MANIFEST="$PROGRAM_ROOT/SOURCE_MANIFEST.sha256"',
            'BUILD_REQUIREMENTS="$PROGRAM_ROOT/packaging/pyinstaller/build-requirements.txt"',
            'validate_build_root',
            'validate_component_manifest',
            'pip check',
            'pip freeze --all',
            'APPIMAGETOOL_SHA256',
            'run_version_smoke_test "final AppImage"',
            '"$PROJECT_MANIFEST"',
            '"$SOURCE_MANIFEST"',
            "Suite component manifest SHA-256:",
            "Project manifest SHA-256:",
            "SOURCE_MANIFEST.sha256 SHA-256:",
        ):
            if fragment not in build_text:
                errors.append(
                    "Fedora builder is missing Suite/provenance integration: "
                    f"{fragment}"
                )

    build_requirements = PACKAGE_ROOT / "packaging/pyinstaller/build-requirements.txt"
    if build_requirements.is_file():
        build_requirement_text = build_requirements.read_text(encoding="utf-8")
        for pinned in (
            "PyInstaller==6.21.0",
            "pyinstaller-hooks-contrib==2026.6",
        ):
            if pinned not in build_requirement_text:
                errors.append(f"Missing pinned build requirement: {pinned}")

    icon_expectations = {
        "maqaronydesk.png": (512, 512),
        "maqaronydesk-about.png": (512, 512),
        "maqaronydesk-master.png": (1024, 1024),
    }
    icon_root = PACKAGE_ROOT / "assets/icons"
    for filename, expected_size in icon_expectations.items():
        path = icon_root / filename
        if not path.is_file():
            errors.append(f"Missing icon: {path.relative_to(ROOT)}")
            continue
        try:
            actual_size = read_png_size(path)
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid icon {path.relative_to(ROOT)}: {exc}")
            continue
        if actual_size != expected_size:
            errors.append(
                f"Wrong icon size {path.relative_to(ROOT)}: "
                f"{actual_size}, expected {expected_size}"
            )

    source_safety_checks = {
        "controllers/file_actions.py": (
            "destination.parent,",
            "def _unique_destination(folder: Path",
            "if clicked not in (keep_both, replace):",
        ),
        "widgets/workspace/dashboard_card.py": (
            "display_name = escape(self.module.display_name)",
            "filename = escape(self.module.filename)",
        ),
        "widgets/editor_lifecycle.py": (
            "return False",
        ),
        "widgets/editor_page.py": (
            "display_name = escape(self.module.display_name)",
            "path_text = escape(str(self.module.path))",
        ),
        "widgets/editor_page_search_view.py": (
            "edit_cursor.beginEditBlock()",
            "self.editor.MAX_DOCUMENT_CHARACTERS",
        ),
        "services/module_scanner.py": (
            'IGNORE_FILE_NAME = ".mepynamu-ignore"',
        ),
        "services/open_document_monitor.py": (
            "class OpenDocumentMonitor(QObject):",
            "self._paths_by_parent: dict[Path, set[Path]]",
            "info = os.stat(path, follow_symlinks=True)",
            "self.path_changed.emit(path)",
        ),
        "models/module_repository.py": (
            "if current is not None and current.loaded:",
            "Workspace discovery does not own the lifetime of a live editor",
        ),
        "services/runtime_paths.py": (
            "with NamedTemporaryFile(",
            'prefix=".marko-plus-write-test-"',
        ),
        "services/config_service.py": (
            "ensure_private_directory(self.path.parent)",
            "tempfile.mkstemp(",
            "os.fsync(handle.fileno())",
            "os.replace(temporary, self.path)",
            "fsync_directory(self.path.parent)",
        ),
        "services/file_io.py": (
            "def read_regular_file(",
            "def current_file_state(",
            "def path_identity_matches(",
            "def rename_path_no_replace(",
        ),
        "widgets/main_window.py": (
            'SHUTDOWN_PROFILE_ENV = "MAQARONYDESK_PROFILE_SHUTDOWN"',
        ),
    }
    for relative, fragments in source_safety_checks.items():
        path = PACKAGE_ROOT / relative
        if not path.is_file():
            errors.append(f"Missing safety-critical source: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in text:
                errors.append(
                    f"Missing safety-critical implementation in {relative}: "
                    f"{fragment}"
                )

    forbidden_tools = (
        "close_performance_check.py",
        "closing_profile_check.py",
        "fast_exit_check.py",
        "grid_scroll_check.py",
        "sidebar_loading_spacing_check.py",
        "sidebar_polish_check.py",
    )
    for name in forbidden_tools:
        if (PACKAGE_ROOT / "qa" / name).exists():
            errors.append(f"Obsolete narrow diagnostic remains: {name}")

    tracked_caches = tracked_python_cache_files()
    if tracked_caches:
        errors.append(
            "Generated Python cache files are tracked by Git: "
            f"{tracked_caches[:5]}"
        )

    local_caches = local_python_cache_paths()

    source_manifest_path = PACKAGE_ROOT / "SOURCE_MANIFEST.sha256"
    manifest_entries: dict[str, str] = {}
    if source_manifest_path.is_file():
        for raw_line in source_manifest_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                digest, relative = raw_line.split("  ./", 1)
            except ValueError:
                errors.append("Invalid SOURCE_MANIFEST.sha256 line")
                continue
            relative_path = Path(relative)
            if (
                len(digest) != 64
                or not relative
                or relative_path.is_absolute()
                or ".." in relative_path.parts
            ):
                errors.append("Unsafe or invalid SOURCE_MANIFEST.sha256 entry")
                continue
            manifest_entries[relative_path.as_posix()] = digest

        expected_source_files: set[str] = set()
        for path in SOURCE_ROOT.rglob("*"):
            if not path.is_file() or path == source_manifest_path:
                continue
            if is_generated_area(path) or is_python_cache_path(path):
                continue
            expected_source_files.add(path.relative_to(SOURCE_ROOT).as_posix())

        if set(manifest_entries) != expected_source_files:
            missing = sorted(expected_source_files - set(manifest_entries))
            stale = sorted(set(manifest_entries) - expected_source_files)
            errors.append(
                "Source manifest file set mismatch; "
                f"missing={missing[:2]}, stale={stale[:2]}"
            )
        for relative, expected_digest in manifest_entries.items():
            source = SOURCE_ROOT / relative
            if source.is_file() and sha256(source) != expected_digest:
                errors.append(f"Source manifest checksum mismatch: {relative}")

    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key)\s*[:=]\s*['\"][^'\"]+"
    )
    for path in ROOT.rglob("*"):
        if is_generated_area(path):
            continue
        if not path.is_file() or path.suffix.lower() in {".png", ".ico", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if secret_pattern.search(text):
            errors.append(f"Possible committed secret in {path.relative_to(ROOT)}")

    # x18.8 SHA preservation gate is historical; it intentionally pins the old
    # toolbar inventory and release identity. The x21.0 gate checks the
    # authoritative icon pack and the newly approved command mapping.
    icon_gate = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x210_toolbar_icons_qa.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if icon_gate.stdout.strip(): print(icon_gate.stdout.strip())
    if icon_gate.returncode:
        errors.append("x21.0 canonical icon-pack and wiring gate: "
                      + (icon_gate.stderr.strip() or icon_gate.stdout.strip()))

    x213_gate = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x213_icon_family_qa.py")],
        capture_output=True, text=True, check=False,
    )
    if x213_gate.stdout.strip(): print(x213_gate.stdout.strip())
    if x213_gate.returncode:
        errors.append("x21.3 Maqa icon families: " + (x213_gate.stderr.strip() or x213_gate.stdout.strip()))

    x212_gate = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x212_exit_toolbar_qa.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if x212_gate.stdout.strip(): print(x212_gate.stdout.strip())
    if x212_gate.returncode:
        errors.append("x21.2 Exit toolbar contract: "
                      + (x212_gate.stderr.strip() or x212_gate.stdout.strip()))

    x211_gate = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x211_icon_wiring_qa.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if x211_gate.stdout.strip(): print(x211_gate.stdout.strip())
    if x211_gate.returncode:
        errors.append("x21.1 icon wiring and unchanged artwork gate: "
                      + (x211_gate.stderr.strip() or x211_gate.stdout.strip()))

    help_headless = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x133_help_actions_headless_check.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if help_headless.stdout.strip(): print(help_headless.stdout.strip())
    if help_headless.returncode:
        errors.append("x13.3 Help actions headless exercise: "
                      + (help_headless.stderr.strip() or help_headless.stdout.strip()))

    # The frozen x13.2 release checker is deliberately kept unchanged. It pins
    # x13.2 identity and the historical MainWindow Help locations, so it is not
    # a valid live gate for x13.3. The x13.3 preservation gate above protects
    # every original x13.2 file, including the old checker and the relocated
    # method bodies. Existing navigation/layout headless checks still run below.

    history_test = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x131_navigation_history_headless_check.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if history_test.stdout.strip(): print(history_test.stdout.strip())
    if history_test.returncode:
        errors.append("x13.1 navigation history headless exercise: "
                      + (history_test.stderr.strip() or history_test.stdout.strip()))

    layout_test = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x132_layout_controls_headless_check.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if layout_test.stdout.strip(): print(layout_test.stdout.strip())
    if layout_test.returncode:
        errors.append("x13.2 layout controls headless exercise: "
                      + (layout_test.stderr.strip() or layout_test.stdout.strip()))

    direct_drop = subprocess.run(
        [sys.executable, str(PACKAGE_ROOT / "qa" / "x121_direct_drop_check.py")],
        cwd=SOURCE_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False, timeout=30,
    )
    if direct_drop.stdout.strip(): print(direct_drop.stdout.strip())
    if direct_drop.returncode:
        errors.append("x12.1 relocated direct-drop wiring gate: "
                      + (direct_drop.stderr.strip() or direct_drop.stdout.strip()))

    if errors:
        print("Release check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if local_caches:
        print(
            "Notice: ignoring locally generated Python cache paths "
            f"({len(local_caches)} found; covered by .gitignore)."
        )

    print(f"MaqaronyDesk {EXPECTED_VERSION} release check passed.")
    return 0


if __name__ == "__main__":
    for qa_name in ("github-readme-lock-qa.py", "halcyon-family-qa.py", "halcyon-dark-import-qa.py", "x216_qa_relocation_check.py", "x217_printsupport_builder_qa.py", "final-100-appimage-qa.py"):
        subprocess.run([sys.executable, str(PACKAGE_ROOT / "qa" / qa_name)], check=True)

if __name__ == "__main__":
    raise SystemExit(main())
