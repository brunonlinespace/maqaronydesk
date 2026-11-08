#!/usr/bin/env python3
"""Immutable GitHub README gate; authoritative original is SHA-256 pinned.
Only current-version field(s) are permitted to vary. Never update this
reference or its fingerprint as part of routine release versioning.
"""
from pathlib import Path
import hashlib, re, sys
root=Path(__file__).resolve().parents[2]
reference=Path(__file__).with_name("github-readme-authority.txt").read_bytes()
assert hashlib.sha256(reference).hexdigest()=="f9af0781a9898b02ce2215474b900b0ca17f7afe2c10a5915fc05e135527659a", "Protected README authority was changed"
expected=reference.decode("utf-8")
assert expected.count("Current release: **1.0.0-x21.4**")==1
expected=expected.replace("Current release: **1.0.0-x21.4**", "Current release: **1.0.0**")
actual=(root/"README.md").read_bytes()
assert actual==expected.encode("utf-8"), "GitHub README differs outside approved version field(s)"
print("PASS immutable GitHub README (version field(s) only)")
