#!/usr/bin/env python3
"""Final 1.0.0 release: execute real builder metadata and version-smoke functions.

No Fedora/PyQt runtime is available in this QA environment. These tests do not
claim a full AppImage build, and intentionally exercise unmodified builder code
by sourcing it in subprocesses with controlled temporary inputs.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'maqarony_desk'
BUILDER = PACKAGE / 'packaging/fedora/build-appimage.sh'
META = PACKAGE / 'packaging/appimage'
VERSION = '1.0.0'

# Desk Health Check is source metadata, not a frozen historical release record.
# Its version and fingerprints must describe the actual promoted source.
import json
health = json.loads((ROOT / 'desk-health-check.json').read_text())
assert health['application']['version'] == VERSION, 'Desk Health Check version is stale'
for rel, digest in health['source_files'].items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, ('Desk Health Check stale hash', rel)

# All relevant version authorities must agree, not just the program launcher.
assert subprocess.run([sys.executable, str(ROOT / 'main.py'), '--version'],
    capture_output=True, text=True, check=True).stdout.strip() == f'MaqaronyDesk {VERSION}'
assert f'APP_VERSION="{VERSION}"' in BUILDER.read_text()
assert f'X-AppImage-Version={VERSION}\n' in (META / 'maqaronydesk.desktop').read_text()
assert f'"version": "{VERSION}"' in (ROOT / 'suite-pythoine-component.json').read_text()
assert f'"version": "{VERSION}"' in (PACKAGE / 'maqaronydesk.json').read_text()
release_xml = META / 'io.github.brunonlinespace.maqaronydesk.metainfo.xml'
release_nodes = ET.parse(release_xml).getroot().findall('./releases/release')
assert [r.attrib['version'] for r in release_nodes] == [VERSION], 'AppStream contains historical/experimental entry or mismatched version'
assert '1.0.0-x21.7' not in BUILDER.read_text(), 'Stale-version builder literal'
assert '1.0.0-x21.7' not in (META / 'maqaronydesk.desktop').read_text()


def invoke(script: str, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(['bash', '-c', 'source "$1"; shift; '+script, 'qa', str(BUILDER), *map(str, args)],
                          text=True, capture_output=True, env=env, timeout=30)


def expect_pass(result: subprocess.CompletedProcess[str], label: str) -> None:
    assert result.returncode == 0, (label, result.returncode, result.stdout[-1600:], result.stderr[-1600:])


def expect_fail(result: subprocess.CompletedProcess[str], label: str) -> None:
    assert result.returncode != 0, (label, result.stdout[-1600:], result.stderr[-1600:])

with tempfile.TemporaryDirectory(prefix='maqdesk-final100-') as td:
    work = pathlib.Path(td)
    copy = work / 'payload'
    copy.mkdir()
    for item in ['AppRun','maqaronydesk.desktop',release_xml.name]:
        shutil.copy2(META/item, copy/item)
    desktop = copy/'maqaronydesk.desktop'
    xml = copy/release_xml.name

    # Real validator functions, not copies or reimplementations.
    expect_pass(invoke('validate_desktop_entry_basic "$1"',desktop), 'valid desktop')
    expect_pass(invoke('validate_appstream_basic "$1"',xml), 'valid AppStream')
    text = desktop.read_text()
    desktop.write_text(text.replace(f'X-AppImage-Version={VERSION}', 'X-AppImage-Version=1.0.0-x21.7'))
    expect_fail(invoke('validate_desktop_entry_basic "$1"',desktop), 'stale desktop version')
    desktop.write_text(text.replace('MimeType=text/markdown;', 'MimeType=text/rtf;'))
    expect_fail(invoke('validate_desktop_entry_basic "$1"',desktop), 'unsupported MIME')
    desktop.write_text(text)

    content=xml.read_text()
    xml.write_text(content.replace('version="1.0.0" date=', 'version="1.0.0-x21.7" date='))
    expect_fail(invoke('validate_appstream_basic "$1"',xml), 'stale AppStream version')
    xml.write_text(content.replace('</releases>', '    <release version="1.0.0-x21.7" date="2026-11-01"/>\n  </releases>'))
    expect_fail(invoke('validate_appstream_basic "$1"',xml), 'historical development entry after final')
    xml.write_text(content)

    baseenv = {**os.environ, 'MAQARONYDESK_ALLOW_ROOT_BUILD':'1',
               'MAQARONYDESK_ALLOW_UNSUPPORTED_HOST':'1', 'PYTHONDONTWRITEBYTECODE':'1'}
    # Source actual check_inputs, requiring valid metadata prior to venv creation.
    expect_pass(invoke('APPIMAGE_PAYLOAD="$1"; check_inputs', copy, env=baseenv), 'real source preflight')
    xml.write_text(content.replace('</releases>', '    <release version="1.0.0-x21.7" date="2026-11-01"/>\n  </releases>'))
    expect_fail(invoke('APPIMAGE_PAYLOAD="$1"; check_inputs',copy,env=baseenv),'preflight bad history')
    xml.write_text(content)

    # When native appstreamcli is present, real failure must terminate preflight.
    bin_dir=work/'bin';bin_dir.mkdir()
    native=bin_dir/'appstreamcli'
    native.write_text('#!/bin/sh\nexit 71\n')
    native.chmod(0o755)
    fakeenv={**baseenv,'PATH':str(bin_dir)+os.pathsep+os.environ['PATH']}
    result=invoke('APPIMAGE_PAYLOAD="$1"; check_inputs',copy,env=fakeenv)
    expect_fail(result,'native validator failure propagation')
    assert 'AppStream validation failed during build preflight' in result.stderr, result.stderr

    # Exercise actual AppDir assembly (the location of the Pad 1.0.0 mistake)
    fake_pyi=work/'pyi';(fake_pyi/'maqaronydesk').mkdir(parents=True)
    fake_bin=fake_pyi/'maqaronydesk'/'maqaronydesk'
    fake_bin.write_text('#!/bin/sh\necho "MaqaronyDesk 1.0.0"\n')
    fake_bin.chmod(0o755)
    appdir=work/'AppDir'
    result=invoke('APPDIR="$1"; PYI_DIST="$2"; assemble_appdir',appdir,fake_pyi,env=baseenv)
    expect_pass(result, 'real AppDir assembly')
    assert (appdir/'usr/share/metainfo'/release_xml.name).read_bytes()==release_xml.read_bytes()

    # Verify actual version smoke function recognizes correct output and rejects stale value.
    smokehome=work/'smoke-home'
    result=invoke('SMOKE_HOME="$1"; run_version_smoke_test "test payload" "$2"',smokehome,fake_bin,env=baseenv)
    expect_pass(result,'actual version smoke pass')
    fake_bin.write_text('#!/bin/sh\necho "MaqaronyDesk 1.0.0-x21.7"\n')
    result=invoke('SMOKE_HOME="$1"; run_version_smoke_test "test payload" "$2"',smokehome,fake_bin,env=baseenv)
    expect_fail(result,'actual version smoke stale version')
    assert 'version smoke test failed' in result.stderr, result.stderr

print('PASS MaqaronyDesk 1.0.0: metadata/preflight native failure, AppDir assembly, exact-version smoke (+negative tests)')
