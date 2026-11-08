#!/usr/bin/env python3
"""x21.2: Exit in the final File Ribbon group; one QAction, existing quit semantics."""
import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
shell=(R/'widgets/shell_ribbon.py').read_text()
win=(R/'widgets/main_window.py').read_text()
cmd=(R/'widgets/editor_commands_appearance.py').read_text()
for name,txt in [('shell_ribbon',shell),('main_window',win),('editor_commands_appearance',cmd)]: ast.parse(txt,filename=name)
assert '[("print_action"), ("export_pdf_action")],\n                [("exit_action")],' in shell
assert 'if index:\n                    toolbar.addSeparator()' in shell
assert '"save_exit_action", "exit_action",' in win
assert 'self.exit_action = self._command("Exit", self.close, QKeySequence.StandardKey.Quit)' in cmd
assert 'shortcut_text = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)' in cmd
assert 'action.setToolTip(f"{label} — {shortcut_text}" if shortcut_text else label)' in cmd
assert '"exit_action":"exit"' in cmd
for scheme in ('light','dark'): assert (R/f'assets/toolbar-icons/{scheme}/exit.png').is_file()
print('PASS x21.2: final File Ribbon Exit, separator, existing action/icon/shortcut tooltip')
