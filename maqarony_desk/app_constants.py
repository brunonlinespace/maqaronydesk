# MaqaronyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared application identity and metadata."""

from maqarony_desk import (
    APP_ID,
    APP_NAME as SUITE_APP_NAME,
    APP_VERSION,
    DESKTOP_ID,
    PUBLISHER_ID,
)

# Visible product branding and canonical Suite/package identity are MaqaronyDesk.
APP_INTERNAL_NAME = "maqaronydesk"
APP_BRAND_NAME = "MaqaronyDesk"
APP_DISPLAY_NAME = APP_BRAND_NAME
APP_WINDOW_TITLE = APP_DISPLAY_NAME
APP_RUNTIME_DESKTOP_ID = DESKTOP_ID
APP_REVISION = "1.0.0-x21.7"

ORGANIZATION_NAME = "brunonlinespace"
ORGANIZATION_DOMAIN = "github.com/brunonlinespace"

MARKDOWN_EXTENSIONS = frozenset({".md", ".markdown", ".mdown", ".mkd"})
MARKDOWN_FILE_GLOB = "*.md *.markdown *.mdown *.mkd"

GITHUB_URL = "https://github.com/brunonlinespace/maqaronydesk"
ISSUES_URL = f"{GITHUB_URL}/issues"
