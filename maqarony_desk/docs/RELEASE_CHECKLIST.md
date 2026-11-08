# MaqaronyDesk 1.0.0 — Final promotion (2026-11-02)

- [x] Source/manifest/desktop/AppStream versions aligned; exact CLI version check.
- [x] AppStream contains final 1.0.0 only; development history preserved in release notes and changelog.
- [x] Builder metadata preflight and negative/malformed metadata tests.
- [x] No editor, workspace or icon changes from x21.7.
- [ ] Fedora 44 full AppImage build and live GUI verification (not available in this environment).

---

# MaqaronyDesk 1.0.0-x21.7 — PrintSupport builder hotfix (2026-11-01)

- [x] PrintSupport preflight targets `widgets/editor_printing.py` and verifies `MainWindow` mixin wiring.
- [x] Existing Qt PrintSupport bundle requirement retained.
- [x] Previous QA suite and migrated QA files preserved.
- [x] Protected GitHub README changed only in its current-version field.
- [ ] End-to-end Fedora 44 AppImage build and live Print/PDF operations.

---

# MaqaronyDesk 1.0.0-x21.6 — QA directory consolidation (2026-11-01)

- [x] All 167 previous `tools/` files remain present in `qa/` and no obsolete directory remains.
- [x] Active release runner and Fedora AppImage preflight resolve from `qa/`.
- [x] Existing icon, navigation, layout, shortcut, README and source-manifest checks pass.
- [x] Protected GitHub README changed only in its current-version field.
- [ ] Live Fedora KDE/PyQt6 startup and builder validation.

---

# MaqaronyDesk 1.0.0-x21.5 — README authority and dark Halcyon filename (2026-11-01)

- Adopt user-approved GitHub README, changing only current-version metadata.
- Rename the dark Halcyon `impport-file.png` to `import-file.png` byte-for-byte.
- Run the mandatory README lock, source manifest and icon filename-parity checks.

---

# MaqaronyDesk 1.0.0-x21.4 — Maqa icon families (2026-11-01)

Added selectable Maqa Icons Harmony (default), Humility, and Heritage. The App Icons submenu follows App Theme in Settings; three mutually exclusive Modern toolbar commands follow theme controls with a separator. Selection persists, refreshes command artwork and available workspace icons, and preserves underlying editor workflows. New family artwork comes directly from the supplied 144-per-theme packs.

---

# MaqaronyDesk 1.0.0-x21.2 — Exit on File toolbar

- [x] Exit action appended last in File Ribbon group after a separator.
- [x] Shared AppMenu QAction uses existing Quit shortcut with tooltip and `exit.png`.
- [x] No icon or editor implementation changed.
- [x] Current static release gate and source manifest verified.
- [ ] Live KDE/PyQt6 command, shortcut, overflow and unsaved-close testing.

---

# MaqaronyDesk 1.0.0-x21.1 — Desk icon wiring correction

- [x] Open External File QAction uses `open.png` in AppMenu and Ribbon.
- [x] Dashboard Edit buttons use `file-launch.png` in list and grid cards.
- [x] Show Sidebar updates `show-sidebar.png` / `show-sidebar-right.png` when dock moves and when theme refreshes; checkbox remains visibility-only.
- [x] All 288 toolbar PNGs retain their x21.0 SHA-256; no other production code changes.
- [x] Static QA and source manifest verified.
- [ ] Confirm live KDE/PyQt6 sidebar docking and palette switching in AppMenu and Ribbon.

# MaqaronyDesk 1.0.0-x21.0 — Grapheme Chars and backing-warning identity

- [x] Unicode extended-grapheme counting of Markdown source, including markup, spaces and logical newlines, with block revision/total caching.
- [x] Cursor movement does not re-extract or re-segment unchanged document text.
- [x] Backing-file messages receive explicit `backing_file` identity, and only that warning clears when the backing path recovers.
- [x] Repository and direct-monitor notification routes unchanged; repeated state notifications suppressed.
- [x] Source preservation against x18.7, all 256 PNGs and other source assets byte-for-byte preserved; zero SVGs.
- [x] Focused Qt-free tests, source syntax, identity, manifest, and archive integrity checks.
- [ ] Full historical release gate (timed out in this environment) and live Fedora KDE/PyQt6 GUI/large-document performance tests.

# MaqaronyDesk 1.0.0-x18.4 — Message parity / ownership

- [x] Four agreed editor-message additions at their existing operations, no change in widgets or geometry.
- [x] Protected Save Version As emits one local, preservation-specific confirmation; no central duplicate.
- [x] Output-verified PDF, existing missing-link paths, mode signals, and monitored backing-state transitions covered by headless QA.
- [x] Original x18.3 source preservation, release metadata and manifest validated.
- [ ] Verify all four message additions and Save Version As in live Fedora KDE/PyQt6.

# MaqaronyDesk 1.0.0-x18.3 — Editor-message ownership

- [x] Connect each EditorPage message signal to its local label before document loading.
- [x] Preserve original failed-initial-load error centrally when no EditorPage survives.
- [x] Route link and paste warnings locally; do not duplicate Save As or lock messages.
- [x] Original editor status geometry, message wording and timeouts, workspace messages and unrelated production methods preserved.
- [x] Current release check, focused Qt-free QA and source manifest synchronized.
- [ ] Live Fedora KDE/PyQt6 verify initial load/failure, Save/Save As, Replace, Locked Mode and multi-page ownership.

# MaqaronyDesk 1.0.0-x18.2 — Open-document crash correction

- [x] Remove only the obsolete encoding-label update in successful `load_from_disk()`.
- [x] Existing consolidated status updater retains encoding/newline values; the successful-load path passes headless execution regression.
- [x] Current release gate and source preservation pass; version metadata and source manifest are synchronized.
- [ ] Verify opening managed Markdown documents and status values in Fedora KDE/PyQt6.

# MaqaronyDesk 1.0.0-x18.1 — Editor status convergence

- [x] Source-level five-field implementation and version metadata.
- [x] Original workspace status bar unchanged.
- [ ] Fedora KDE/PyQt6 check of editor heights, narrow window width, and timing of messages.

---

# MaqaronyDesk 1.0.0-x17.2 — Mixed-newline tie-breaking

- [x] Only `_detect_newline_style()` changes in production code, matching MaqaronyPad's exact branch/counting sequence.
- [x] x17.1 source preservation, x17.1 Properties and x17.0 Preview Only regression checks pass; encoding/BOM and save implementations are unchanged.
- [x] CRLF/LF/CR count/tie/default cases and the current static release checks pass.
- [x] Release identities, AppStream, Suite/Health Check metadata and source manifest correspond to x17.2.
- [ ] Verify encoding/newline preservation with actual document round trips in Fedora KDE/PyQt6.
- [ ] Test portable and AppImage GUI execution on the target host.

# MaqaronyDesk 1.0.0-x17.1 — Properties modification date

- [x] Only the datetime import and Properties Modified assignment change in production code; the rest of the Properties method and application remain unchanged.
- [x] Exact x17.0 source preservation and x17.0 Preview Only replacement regression tests pass.
- [x] Local date/time formatting, fresh file-stat selection and unavailable-file fallback pass Qt-free checks.
- [x] Release identities, AppStream, Suite/Health Check metadata, focused QA and source manifest correspond to x17.1.
- [ ] Verify readable modification dates and unchanged fields in the live Fedora KDE/PyQt6 Properties dialog.
- [ ] Test portable and AppImage GUI execution on the target host.

# MaqaronyDesk 1.0.0-x17.0 — Preview Only replacement protection

- [x] Only `replace_current` and `replace_all` gain the agreed Preview Only early-return guards, after existing Locked Mode checks.
- [x] Source/Split replacement behavior, source editor, preview renderer, Dashboard, document lifecycle and all other production methods are unchanged.
- [x] Existing historical QA scripts remain byte-for-byte unchanged; new x17.0 scope/behavior regression tests pass.
- [x] Package/Suite/AppStream/Health Check versions, source manifest and ZIP checksums correspond to x17.0.
- [ ] Verify Replace/Replace All refusal, Find navigation, Locked Mode and normal editable modes on Fedora KDE/PyQt6.
- [ ] Test portable and AppImage GUI execution on the target host.

# MaqaronyDesk 1.0.0-x16.2 — Dashboard actions checklist

- [x] Only Edit and Preview buttons constructed for main/folder List/Grid Dashboard cards.
- [x] Edit loads `open.png` in both icon palettes; Preview retains `preview-only.png`.
- [x] Edit routes through last-editable `source`/`split` preference, including card double-click.
- [x] Preview continues to use existing Preview Only mode without changing editor lock state.
- [x] Source-preservation check against exact x15.3 archive and headless compatibility checks pass.
- [x] Source hashes and Desk Health Check / Suite manifests validate.
- [ ] Verify button icons/labels and existing controls on Fedora KDE/PyQt6.
- [ ] Portable/AppImage GUI smoke test on target host.

# MaqaronyDesk 1.0.0-x15.3 — Dashboard visibility batching checklist

- [x] Exact x15.2 source inventory preserved apart from this edition's approved files.
- [x] New x15.3 headless Dashboard QA passes and old x15.2 QA is retained unchanged.
- [x] Embedded Desk Health Check manifest and Suite metadata identify 1.0.0-x15.3.
- [x] Source static release gate and archive checks pass.
- [ ] Run Fedora KDE / PyQt6 search clear and startup tests with 700 nested documents.
- [ ] Compare x15.2 to x15.3 using Desk Health Check 2.1 before claiming latency improvement.

# MaqaronyDesk 1.0.0-x15.2 — Shutdown and Health Check release checklist

- [ ] Portable `python main.py --version` prints `MaqaronyDesk 1.0.0-x15.2`.
- [ ] Close a fully loaded 700-file workspace without rebuilding Dashboard List/Grid cards.
- [ ] Cancel an unsaved-document exit and verify all state and editor contents remain intact.
- [ ] Exercise scanner-stop timeout: abort close, restore Dashboard, allow retry.
- [ ] Close with active scanning, verify cancellation and no unexpected data loss.
- [ ] Confirm original x14.0 palette/Folder Dashboard display remains unchanged.
- [ ] Validate embedded desk-health-check.json and suite-pythoine-component.json using Desk Health Check 2.0.
- [ ] Static QA, source manifest and extracted ZIP checks pass; live KDE/AppImage regression tests still required.

---

# MaqaronyDesk 1.0.0-x15.2 — Main Dashboard card appearance checklist

- [ ] Portable `python main.py --version` prints `MaqaronyDesk 1.0.0-x15.2`.
- [ ] Root Dashboard List/Grid cards use QPalette.Button, QPalette.Mid and 6px rounded native-style panels.
- [ ] No selected-card styling, no change to card actions or sorting.
- [ ] Folder Dashboard source and its original card appearance are unchanged.
- [ ] System → Dark → Light → System repaints existing root cards without stale text/button palettes.
- [ ] Current source gate and ZIP-extracted gate pass; live Fedora KDE/AppImage tests remain required.

# MaqaronyDesk 1.0.0-x13.4 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x13.4`.
- [ ] The renamed `widgets/theme.py` is byte-identical to the 1.0.0-x13.3 theme implementation.
- [ ] All direct theme imports resolve at the new name; the old filename is absent.
- [ ] Current provenance, headless and static release checks pass; historical records remain unchanged.
- [ ] Verify Light/Dark/System and theme switching on Fedora KDE; AppImage smoke test remains required.

---

# MaqaronyDesk 1.0.0-x13.3 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x13.3`.
- [ ] `python maqarony_desk/qa/x133_help_actions_convergence_check.py` passes.
- [ ] `python maqarony_desk/qa/x133_help_actions_headless_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies against this source edition.
- [ ] Quick Tour initial/reuse/close, shortcut catalogue and dialog, bundled docs, GitHub/Issues and About are exercised on Fedora KDE/PyQt6.
- [ ] Portable and AppImage tests pass on target host.

---

# MaqaronyDesk 1.0.0-x13.2 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x13.2`.
- [ ] `python maqarony_desk/qa/x132_layout_controls_convergence_check.py` passes.
- [ ] `python maqarony_desk/qa/x132_layout_controls_headless_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies against the current source edition.
- [ ] Sidebar left/right width, sidebar/status/file-header toggles, Focused Mode and fullscreen restoration work on Fedora KDE/PyQt6.
- [ ] Portable launch and AppImage tests pass on target host.

---

# MaqaronyDesk 1.0.0-x13.1 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x13.1`.
- [ ] `python maqarony_desk/qa/x131_navigation_history_convergence_check.py` passes.
- [ ] `python maqarony_desk/qa/x131_navigation_history_headless_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies against the current source edition.
- [ ] Back button and mouse Back navigate among Dashboard, folders and documents correctly; invalid/deleted paths are skipped on Fedora KDE/PyQt6.
- [ ] Portable launch and AppImage tests pass on target host.

---

# MaqaronyDesk 1.0.0-x13.0 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x13.0`.
- [ ] `python maqarony_desk/qa/x130_document_tabs_convergence_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies from the source root.
- [ ] Tabs enabled/disabled, close/rebind, temporary Dashboard/folder tabs and tab shortcuts work in Fedora KDE/PyQt6.
- [ ] Portable launch and AppImage checks pass on the target host.

---

# MaqaronyDesk 1.0.0-x12.1 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x12.1`.
- [ ] `python maqarony_desk/qa/x121_workspace_dialog_convergence_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies from the source root.
- [ ] Workspace Dashboard/Navigation, dialogs, icon themes and file-safety flows tested in Fedora KDE/PyQt6.
- [ ] Portable launch and AppImage checks completed on target host.

---

# MaqaronyDesk 1.0.0-x12.0 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 1.0.0-x12.0`.
- [ ] `python maqarony_desk/qa/x1_editor_widgets_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies from the source root.
- [ ] Live Markdown highlighting, line-number margins, editing and workspace tests pass in PyQt6.

---

# MaqaronyDesk 0.5.0 Release Checklist

- [ ] `python main.py --version` reports `MaqaronyDesk 0.5.0` when PyQt6 is available.
- [ ] Edit contains Toggle Comment after Delete and before Duplicate Line/Selection.
- [ ] Edit → Toggle Comment visibly carries `Ctrl+/` through its QAction shortcut.
- [ ] Toggle Comment is no longer duplicated as a menu-less Keyboard Shortcuts entry.
- [ ] 0.4.16 File Ribbon and More Actions ordering remains unchanged.
- [ ] `python maqarony_desk/qa/maqarony_desk_0_5_0_check.py` passes.
- [ ] `python maqarony_desk/qa/release_check.py` passes.
- [ ] `SOURCE_MANIFEST.sha256` verifies from the source root.

## x11.1 historical integrity and packaging

- [ ] `python -m maqarony_desk.qa.x111_history_and_identity_check` passes, proving both historical source origins against fixed SHA-256 fingerprints.
- [ ] The original Marko Plus 0.4.17 changelog and release notes match their archive hashes and remain intact suffixes of current history.
- [ ] Fedora dependency/test script entry points execute directly; AppRun is installed executable by the builder.
- [ ] Actual Fedora AppImage and KDE/Plasma GUI tests are completed on the target host before public release.
