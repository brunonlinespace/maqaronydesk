#!/usr/bin/env python3
"""Regression: portable top-level main.py stays executable on Unix."""
import os
from pathlib import Path
p=Path(__file__).resolve().parents[2]/"main.py"
assert p.is_file()
assert p.read_bytes().startswith(b"#!/usr/bin/env python3\n")
assert p.stat().st_mode & 0o111 == 0o111, "main.py must have chmod +x"
print("PASS x6.1: MepyNamu main.py executable, shebang retained")
