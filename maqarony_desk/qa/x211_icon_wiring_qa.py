#!/usr/bin/env python3
"""x21.1: exact icon wiring with source-only, asset-preservation guards."""
from pathlib import Path
import hashlib, json, ast
PKG=Path(__file__).resolve().parents[1]
WIDGETS=PKG/'widgets'
source=(WIDGETS/'editor_commands_appearance.py').read_text(encoding='utf-8')
layout=(WIDGETS/'window_parts/layout_controls.py').read_text(encoding='utf-8')
card=(WIDGETS/'workspace/dashboard_card.py').read_text(encoding='utf-8')
for path in (WIDGETS/'editor_commands_appearance.py',WIDGETS/'window_parts/layout_controls.py',WIDGETS/'workspace/dashboard_card.py'):
    ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
assert '"open_external_file_action":"open"' in source
assert '"open_external_file_action":"open-external-file"' not in source
assert '(self.edit_button, "file-launch")' in card
assert '(self.edit_button, "open")' not in card
assert '"sidebar_action":self._sidebar_toggle_icon_name()' in source
assert 'return "show-sidebar-right" if position == "right" else "show-sidebar"' in source
assert 'position = self._sidebar_position()' in source
assert 'position = str(self.config.get("sidebar_position", "left"))' in source
assert 'self.sidebar_action.setIcon(QIcon(str(path)) if path.is_file() else QIcon())' in source
assert 'self._refresh_sidebar_toggle_icon()' in layout
assert layout.index('self._set_splitter_sidebar_width(sidebar_width)') < layout.index('self._refresh_sidebar_toggle_icon()') < layout.index('def _set_sidebar_visible(')
assert 'self.sidebar_action.setChecked(visible)' in layout
assert 'self.sidebar_action.blockSignals(True)' in layout
# Canonical x21.0 icon hashes are immutable; no new or removed files allowed.
ref=json.loads((PKG/'qa/x210-toolbar-inventory.json').read_text())
base=PKG/'assets/toolbar-icons'
actual={p.relative_to(base).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*.png')}
assert actual==ref, 'x21.1 changed canonical x21.0 icon artwork/inventory'
assert len(ref)==288
for p in ('open','file-launch','show-sidebar','show-sidebar-right'):
    for scheme in ('light','dark'):
        assert f'{scheme}/{p}.png' in ref
print('PASS: x21.1 Desk-specific icon wiring, dock-aware shared QAction, visibility state, exact 288-PNG preservation')
