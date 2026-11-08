### x18.5 — Dashboard drag-move stylesheet guard

- Drag external Markdown over the root Dashboard and a Folder Dashboard. The border should appear once on entry, remain during movement, and clear after leave or drop; existing file handling must work unchanged.
- Move the pointer repeatedly within either target, including dense workspaces. The guard must not reapply an identical stylesheet.
- Verify disallowed file drags are ignored, and accepted Markdown files use the existing Copy action and destination handling.
- Run `python -m maqarony_desk.qa.release_check` and `python -m maqarony_desk.qa.x185_drag_highlight_qa`; run Fedora KDE/Wayland GUI regression separately.

### x18.2 — Successful document load after two-label status correction

- Open a valid managed Markdown document. Confirm no obsolete `encoding_status_label` access and that the consolidated indicator shows the file encoding and newline style.
- Confirm that the successful-load pipeline still refreshes search and preview, and emits its existing Loaded message.
- Run `python -m maqarony_desk.qa.release_check` and the dedicated x18.2 headless regression; verify actual Fedora KDE/PyQt6 document opening separately.

### x18.1 — Two-label status and editor-page geometry

- Editor messages occupy one flexible label at left; a single permanent right-aligned label shows Insert/Overwrite · Line/Column/total Chars · Encoding/Newline · Source/Split/Preview and numerical Zoom. Preserve thousands separators and prior message timeouts.
- Eliminate the expanding statistics label and excess horizontal gaps without adding new style or min-width reservations.
- Restore the editor page's 12-px bottom margin; retain existing 8-px internal content spacing and use zero spacing immediately above the editor status bar, following RiqatonyDesk geometry. Workspace status bar and window/splitter behavior unchanged.
- Static QA required; live Fedora KDE visual and narrow-window validation remains outstanding.

### x18.0 — Editor status-bar convergence

Current static checks verify the five logical status fields, message isolation, live updates, x17.2 historical protections, and no workspace status-bar edits. Live GUI geometry checks remain required.

### x17.2 — Pad-authoritative newline detection

- Open mixed-newline Markdown with CRLF, LF and CR examples: choose the highest-count style; a tie including a nonzero CRLF maximum selects CRLF; a CR/LF-only tie selects LF; no newline selects LF.
- Verify single-style CRLF, LF and CR documents, and source with no terminators. Confirm the saved newline style and UTF-8/UTF-16 BOM/encoding behavior are unchanged except for the agreed tie-selection case.
- Confirm x17.1 Properties formatting and x17.0 Preview Only replacement guard remain intact.
- Run `python -m maqarony_desk.qa.release_check`. Verify actual Markdown open/save/round trips and Qt GUI on Fedora KDE separately.

### x17.1 — Properties modification date

- For a managed Markdown file, open Properties and verify **Modified** displays its disk modification date as `YYYY-MM-DD HH:MM:SS TZ`, not a raw Unix timestamp.
- Change the file's on-disk mtime independently of any cached workspace metadata: Properties must use the current `stat().st_mtime`.
- Verify the existing `Unavailable` fields for a missing/unreadable file, and unchanged Name, Location, Full path, Size, Permissions and Document fields.
- Verify x17.0 Preview Only Replace protection remains; run `python -m maqarony_desk.qa.release_check`. Confirm the actual Qt dialog on Fedora KDE separately.

### x17.0 — Preview Only Find/Replace protection

- Open a managed Markdown document in Preview Only, keep the Find/Replace panel available, and attempt Replace and Replace All: neither may change underlying Markdown or mark the document dirty.
- Confirm Find Next/Previous and search highlighting remain available; confirm Replace and Replace All still edit normally in Source Only and Source + Preview.
- Confirm Locked Mode retains its existing protective prompt and that returning from Preview Only restores normal editable behavior.
- Run `python -m maqarony_desk.qa.release_check` for the Qt-free gate (including x16.2 scroll and x16.0 Dashboard preservation); verify live KDE/PyQt6 separately.

# MaqaronyDesk QA Guide

## Bug report essentials

Include the MaqaronyDesk version, source/AppImage mode, Linux distribution,
desktop environment, X11/Wayland session, exact steps, expected behavior,
actual behavior, and relevant terminal output.

## High-value regression sequences

### Large Workspace

- Open a Workspace containing hundreds or thousands of Markdown documents.
- Switch List/Grid repeatedly and scroll through the final row.
- Resize the sidebar and change folders while scanning or filtering.
- Confirm inactive registered Workspaces are not merged into the active view.

### Editor and preview

- Open documents in Source, Split, and Preview layouts.
- Move among files and verify view-only and editor preferences persist.
- Exercise large Select All/Paste, Replace All, Undo, and Redo operations.
- Verify preview links remain blue before and after activation in both canvas
  schemes.

### Files and folders

- Create a document in the Workspace Dashboard, a folder dashboard, and beside
  an active document; confirm each uses the intended folder.
- Rename and move documents repeatedly, including same-folder drops.
- Rename a folder with F2 and verify open pages/tree paths remain coherent.
- Drop external Markdown files on root and nested destinations; exercise
  Replace, Keep Both, and Skip.

### Save safety

- Save normally, through Save and New, Save and Dashboard, and Save and Exit.
- Modify or replace a file externally before saving and verify MaqaronyDesk does
  not silently overwrite the changed target.
- Close an unsaved prompt using Cancel and the window close control.

### Workspace switching and shutdown

- Switch via **File > Workspace(s)** and **Open / Manage Workspaces...**.
- Verify Dashboard/folder context shows `Workspace — MaqaronyDesk`, and an active document shows `filename — Workspace — MaqaronyDesk` with the Rico-style dirty/locked state markers; verify the Dashboard refreshes.
- Test Dashboard and Last File launch-screen settings independently per app.
- Close during an active scan and with unsaved documents.

## Identity/provenance gate

| Check | Expected result |
| --- | --- |
| `python main.py --version` | `MaqaronyDesk 0.0.1-r3` |
| `maqarony_desk.json` | Canonical name, ID, version, publisher, and desktop ID |
| `python -m maqarony_desk.qa.release_check` | Identity, inventory, hashes, and source checks pass |
| About dialog | MaqaronyDesk 0.0.1-r3, the official Plus logo, and complete unclipped text |

## 0.4.2 MepySivu editor-realignment gate

Run `python -m maqarony_desk.qa.marko_plus_0_4_2_check` to verify the restored MepySivu zoom, Source/Preview split persistence, printable relative-resource Base URL, Paste as Markdown feedback, narrow legacy Ricopad stripping, MepySivu defaults, preserved core editor/preview hashes, and the deliberate exclusion of Audit Item 8 and status-bar work.

## 0.4.1 icon-family gate

Run `python -m maqarony_desk.qa.marko_plus_0_4_1_check` to verify the 0.4.1 semantic icon mapping, 121-icon light/dark families, 64×64 RGBA assets, preserved 36×36 Ribbon geometry, and protected 0.3.10 production baseline.


### x16.2 — Source editor end-of-file scrolling

- Scroll to the final line of short and long Markdown source files, including wrapped and unwrapped text; verify there is no unnecessary viewport-sized blank region beyond the document end.
- Verify wheel, scrollbar, PgDown and End navigation; verify explicit Go To Line retains its existing centering behavior.
- Verify line-number gutter remains aligned when horizontal scrolling becomes available and Source/Split/Preview modes remain unchanged.
- Run `python -m maqarony_desk.qa.release_check` for the x16.2 Qt-free scope check. Runtime confirmation on Fedora KDE/Wayland remains required.
