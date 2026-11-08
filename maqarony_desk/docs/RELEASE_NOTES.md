# MaqaronyDesk 1.0.0 — Final source release (2026-11-02)

Final 1.0.0 source promotion from x21.7; no production editor or workspace changes. Single current final AppStream release; history remains documented here and in CHANGELOG. Builder now runs desktop/AppStream validation during preflight, plus mandatory version-contract regression. Full Fedora AppImage build and live KDE behavior require target-host validation.

---

# MaqaronyDesk 1.0.0-x21.7 — PrintSupport AppImage preflight correction (2026-11-01)

- Correct Fedora builder source preflight: Print/Export PDF depend on `widgets/editor_printing.py` through `EditorPrintingMixin`, not direct imports in `widgets/main_window.py`.
- Preserve mandatory Qt PrintSupport bundle validation and all actual Print/Export PDF behavior.
- Add release-gate coverage that checks mixin ownership, actual PrintSupport imports and PDF output enum; no production runtime sources changed.
- GitHub README modified solely in its current-release field.

---

# MaqaronyDesk 1.0.0-x21.6 — QA directory consolidation (2026-11-01)

- Relocate all 167 QA scripts and fixtures from `tools/` into `qa/`, and remove `tools/`. No production runtime logic changes.
- Update the active release checker, Fedora AppImage builder, and documented QA command paths; preserve the historical fixture contents.
- Test the relocated checks and release gate, including README immutability and artwork inventories.

---

# MaqaronyDesk 1.0.0-x21.5 — Protected README and Halcyon asset correction (2026-11-01)

- Replace the GitHub README with the user-approved updated copy, changing only current-version metadata. Save the supplied bytes as the independently pinned README authority.
- Rename dark Halcyon `impport-file.png` to `import-file.png` without modifying the PNG contents. Validate that both Halcyon themes contain the exact same 144 filenames.
- Preserve all other icon families, command wiring, configuration and editor functionality.

---

# MaqaronyDesk 1.0.0-x21.4 — Halcyon icon family and GitHub README protection (2026-11-01)

- Add Maqa Icons Halcyon to Settings → App Icons, using `assets/toolbar-icons-aero`. The new radio choice has no icon or toolbar command.
- Preserve the previous icon families, family settings, toolbar controls, editor and file-handling behavior.
- Restore the root GitHub README to its protected wording, allowing only the current-version field(s) to change. Archive recovered historical README changes in `docs/history/`; add a mandatory reference-checksum QA gate.
- Static source gates passed; live KDE/PyQt6 GUI behavior remains unverified.

---

## Earlier release notes (x21.3)

# MaqaronyDesk 1.0.0-x21.3 — Maqa icon families (2026-11-01)

Added selectable Maqa Icons Harmony (default), Humility, and Heritage. The App Icons submenu follows App Theme in Settings; three mutually exclusive Modern toolbar commands follow theme controls with a separator. Selection persists, refreshes command artwork and available workspace icons, and preserves underlying editor workflows. New family artwork comes directly from the supplied 144-per-theme packs.

---

# MaqaronyDesk 1.0.0-x21.2 — Exit on File toolbar (2026-10-31)

- Expose the **existing Exit QAction** as the **final command** in the File Ribbon tab, after a separator.
- Use the already-packaged `exit.png` light/dark icons and existing Quit shortcut (`Ctrl+Q` on Linux) in its tooltip.
- Keep AppMenu Exit, close confirmation, workspace state, icon assets and all other commands unchanged.
- Static source check for File-tab order, action identity, icon mapping and shortcut tooltip; live PyQt6/KDE testing remains pending.

---

# MaqaronyDesk 1.0.0-x21.1 — Desk icon wiring correction (2026-10-31)

A narrow source-only follow-up to x21.0. Open External File uses `open.png`; Dashboard-card Edit uses `file-launch.png`; Show Sidebar switches between `show-sidebar.png` (left dock) and `show-sidebar-right.png` (right dock) in the shared QAction used by Ribbon and AppMenu. Dock changes update the artwork immediately; changing theme refreshes the correct icon. Visibility check state, file actions, layouts, configuration semantics and all 288 icon PNGs remain unchanged. Live KDE/PyQt6 UI testing is outstanding.

---

# MaqaronyDesk 1.0.0-x21.0 — canonical toolbar icon pack (2026-10-31)

Icon-only release from 1.0.0-x18.8: replaced the toolbar-icons light/dark collections with the 144-per-theme supplied pack (no retained old assets). Editor Layout uses `layout-markdown.png`; the Light/Dark/System actions use `theme-light.png`/`theme-dark.png`/`theme-system.png`; the Insert > Link AppMenu group uses `link-group.png`. Editor and file workflows are otherwise unchanged.

---

## 1.0.0-x21.0 — Grapheme Chars and backing-warning identity

- Count Unicode extended grapheme clusters in literal Markdown source; one logical newline per block boundary. Cache text-block counts by revision and document total until textChanged. No recount on cursor-only movement.
- Tag backing-file critical messages explicitly. Resolve only a tagged backing-file warning when backing state normalises; preserve unrelated warnings and existing banner/monitor signals.
- No SVG assets; preserve PNGs, editor/layout/file lifecycle, existing messages and document-size limits.
- Qt-free focused tests/static release checks; interactive Fedora KDE/PyQt6 verification remains outstanding.

## 1.0.0-x18.7 — Critical-message recovery and filename-suggestion correction

- Correct the editor critical-message latch on backing-file recovery and explicit clearing. Change protected Save Version As suggested filenames from `- Marko Version` to `- Desk Version` while preserving numbering, extension and collision avoidance.
- Preserve existing document operations, message wording/durations, banners, drop handling, layout and workspace behavior.

## 1.0.0-x18.6 — Desk message-conventions convergence

Shared four-second transient status convention and persistent unresolved warnings; filenames on saves, action-specific duplicate/delete/rename wording, sentence-final punctuation, product identity and duplicate-message correction. No changes to routing, editor features, geometry or drag-and-drop.

## 1.0.0-x18.5 — Drag-highlight stylesheet guard

- Dashboard and Folder Dashboard update their existing drag highlight stylesheet only when the requested style differs from the currently applied stylesheet.
- Preserve the exact highlight appearance, accepted Markdown MIME paths, drag/drop operations, import routing and all unrelated behavior.
- Add x18.5 focused drag-move no-repolish regression and strict x18.4 production-preservation gate. Live Fedora KDE/Wayland validation remains necessary.

## 1.0.0-x18.4 — Message coverage and protected Save Version As ownership

- Add PDF-export completion feedback only for newly written, non-empty PDF output; use RiqatonyDesk's existing confirmation text and the MaqaronyPad x14.2 output verification guard.
- Add missing-local-link feedback to the originating Markdown preview/editor. Preserve the existing external-link handling.
- Report Insert/Overwrite transitions through the existing editor status message with the MaqaronyPad message text and duration.
- Report externally detected backing-file changed/missing transitions once per state change, preserving the current persistent banner and not announcing in-app file operations as external.
- Show protected Save Version As preservation wording through the existing document-local success message, instead of the generic local confirmation followed by a central one.
- No other operation, interface geometry, message wording, theme, workspace or file lifecycle change. Static release gate and focused QA; live Fedora KDE verification remains outstanding.

### 1.0.0-x18.3 — Editor-message ownership correction

- Deliver existing editor-generated messages locally, including initial document loads, replacements, paste/link warnings, save and Save As. Do not relay them into the central workspace bar.
- Preserve the exact initial-load failure wording at the central Desk when the failed editor page cannot be retained.
- Eliminate duplicate Save As / Locked Mode messages and suppress routine lock-state synchronization feedback; preserve user-triggered lock feedback.
- Leave message wording, timeouts, two-label status-bar layout, window geometry, workspace messages, file operations and all unrelated production code unchanged.
- Add focused x18.3 message-routing and method-preservation QA. Fedora KDE/PyQt6 interactive verification remains outstanding.

### 1.0.0-x18.2 — Document-opening crash correction

- Fix an abort when opening a valid Markdown document by removing the obsolete encoding-label access left behind by x18.1. The existing consolidated status indicator already displays encoding and newline information.
- No other editor, status-bar, workspace or layout changes. Run headless document-opening regression QA and release checks; confirm live Fedora KDE document open separately.

### 1.0.0-x18.1 — Two-label editor status correction

- Editor messages occupy one flexible label at left; a single permanent right-aligned label shows Insert/Overwrite · Line/Column/total Chars · Encoding/Newline · Source/Split/Preview and numerical Zoom. Preserve thousands separators and prior message timeouts.
- Eliminate the expanding statistics label and excess horizontal gaps without adding new style or min-width reservations.
- Restore the editor page's 12-px bottom margin; retain existing 8-px internal content spacing and use zero spacing immediately above the editor status bar, following RiqatonyDesk geometry. Workspace status bar and window/splitter behavior unchanged.
- Static QA required; live Fedora KDE visual and narrow-window validation remains outstanding.

### 1.0.0-x18.0 — Five-field editor status convergence

- Editor only: Insert/Overwrite; line/current total, column and total Chars; Source/Split/Preview and Zoom; Encoding/Newline; independently visible Messages. No Words or cursor-offset-as-Char. Preserve numeric grouping.
- Follow RiqatonyDesk editor status bar size-grip and layout sizing, without changing the workspace status bar, window geometry or splitters.
- Static/source verification; live Fedora KDE/PyQt6 visual and window-minimum testing outstanding.

### 1.0.0-x17.2 — Pad-authoritative mixed-newline tie-breaking

- Adopt MaqaronyPad 1.0.0-x13.0's exact newline-style selection sequence in `EditorLifecycleMixin._detect_newline_style()`: count CRLF, remove CRLF for standalone CR/LF counts, prefer CRLF in a top-count tie when present, otherwise select CR only when its count strictly exceeds LF, and use LF by default.
- Change only the newline-detection decision method; do not modify encoding, BOM, file loading/saving, serialization, document state or editor/UI workflows. Preserve x17.0 Preview Only replacement protection and x17.1 Properties formatting.
- Add a Qt-free authoritative-source parity and newline edge-case test with a full x17.1 production/QA preservation gate. Interactive Fedora KDE/PyQt6 and real-file round-trip confirmation remains outstanding.

### 1.0.0-x17.1 — Properties modification-date formatting

- Format Properties → File → Modified from the file's current `stat().st_mtime`, using MaqaronyPad's existing local timestamp format (`YYYY-MM-DD HH:MM:SS TZ`) instead of showing the workspace model's raw Unix timestamp.
- Keep the same Properties dialog layout, File/Document fields, permissions/size display, missing-file fallback, and all editor/workspace behavior. Preserve x17.0 Preview Only replacement protection.
- Add a narrowly scoped Qt-free Properties formatting and x17.0 preservation gate. Live Fedora KDE/PyQt6 dialog verification remains outstanding.

### 1.0.0-x17.0 — Preview Only replacement protection

- In `EditorPageSearchViewMixin.replace_current()` and `replace_all()`, refuse replacement while `view_mode == "preview"`, matching the existing MaqaronyPad Preview Only protection.
- Preserve the existing Locked Mode prompt, source/split replacements, Find/navigation, text limits, search refresh, Preview rendering, Dashboard actions, and all document/workspace lifecycle behavior.
- Add a focused Qt-free test for rejected Preview Only replacement, continuing Source/Split operations and code preservation from x16.2. Fedora KDE/PyQt6 GUI verification remains outstanding.

### 1.0.0-x16.2 — Source editor end-of-file scrolling

- Disable Qt automatic centered overscrolling in the embedded Markdown source editor (`setCenterOnScroll(False)`), matching Sheepy Pad 0.4.1 and MaqaronyPad x12.6.
- Do not change source/preview layouts, scrolling algorithms, word wrapping, line-number gutter, explicit Go To Line centering, Dashboard actions or workspace lifecycle.
- Update current edition metadata, source and Health Check checksums, and a focused Qt-free release gate. Native KDE editor scrolling still requires interactive verification.

### 1.0.0-x16.0 — Dashboard Edit / Preview actions

- Main and Folder Dashboard List/Grid cards now expose only Edit and Preview; remove the Split View card button. The existing editor Split View control remains unchanged.
- Edit uses the existing `markopad_last_editable_view_mode` (`source` or `split`), falling back to the current editable view, otherwise `split`; double-click follows Edit.
- Edit uses the existing light/dark `open.png`; Preview preserves `preview-only.png`, its label and its existing Preview Only routing. No Locked Mode or lock-setting changes.
- Preserve x15.0–x15.3 Dashboard and file-lifecycle code; no caching, scanner, navigation or editor-mode changes.
- Current-edition headless QA verifies source preservation, routing and card actions. Native Fedora KDE button/interaction QA remains to be performed.

### 1.0.0-x15.3 — Corrective Dashboard visibility batching (performance only)

- Batch retained-card hide/show transitions with both Dashboard layouts temporarily suspended and host repainting disabled. Restore each layout and host to its previous enabled state using a `finally` block, then use the existing geometry invalidation once.
- Targets the measured x15.2 startup/scan-completion and search-reset regressions without changing x15.2 ordered-grid retention, widget membership, filtering semantics, sort keys, file management, or x15.0/x15.1 improvements.
- Historical x15.2 QA and releases are preserved. Current-edition headless QA validates batched visibility, search reset, unchanged sort, exception-safe restoration, full source preservation and embedded Health Check manifest.
- This source-only environment cannot validate the actual Fedora KDE/Wayland performance recovery; compare x15.2 and x15.3 with Desk Health Check 2.1 before accepting the performance objective.

### 1.0.0-x15.2 — Dashboard search and sort layout optimisation (performance only)

- Search changes hide or reveal retained cards in-place instead of removing and reinserting both complete List/Grid collections.
- Keep widget layouts in repository sort order independently of the current search. Reorder only when the actual document order or membership changes; a no-op sort does not rebuild layouts. Preserve the historical full-detach method as an unused compatibility hook for Desk Health Check 2.1.
- Reuse grid layout items while reordering; exclude hidden cards from grid wrapping and minimum-size geometry, matching native QVBoxLayout visibility semantics.
- Preserve all x15.1 geometry caching and x15.0 shutdown behaviour, Dashboard actions, file lifecycles, folder dashboards and loading/scanning policy.
- Qt runtime performance still requires Fedora KDE testing through Desk Health Check 2.1.

### 1.0.0-x15.1 — Dashboard List/Grid geometry (performance only)

- Cache active Dashboard page geometry hints by viewport width. Invalidate when Qt requests a layout/style change and after filtering/sorting the cards.
- Remove duplicate geometry notifications when switching List/Grid, retaining the existing QWidget collections and QStackedWidget behaviour.
- Keep x15.0 shutdown optimisation and all file/RTF/Markdown lifecycle behaviour unchanged. No new Dashboard scope or lazy cards.
- Static validation only here; actual Fedora KDE performance requires measurements.

# MaqaronyDesk 1.0.0-x15.0 — Shutdown Dashboard rebuild avoidance (2026-10-21)

- Avoid the unconditional Dashboard set_loading(False) call on successful shutdown, because that call rebuilds both Dashboard card layouts immediately before exit.
- Preserve navigation loading cleanup, the closing dialog, saved workspace/preferences, unsaved-document confirmation, scanner cancellation timeout and explicit process exit.
- On scanner-stop failure, restore the normal Dashboard loading state before returning to the interactive window; this retains the previous rollback path.
- Introduce source-root `desk-health-check.json` matching the existing Suite compatibility metadata, using the Desk Health Check 2.0 family adapter contract.
- No card painting, search, sort, scan, editor, folder Dashboard, preferences or document-lifecycle changes. Historical QA and archived notes are unchanged.
- Static source and compatibility tests pass; Fedora KDE/PyQt6 runtime and AppImage performance testing remain required.

---

# MaqaronyDesk 1.0.0-x14.0 — Main Dashboard palette card appearance (20 October 2026)

- Apply Suite Pythoine 0.11.2 palette-based, antialiased Button/Mid rounded panel painting to the main Dashboard List/Grid cards only.
- No selected-card visual highlight; keep existing buttons, commands, layouts, interaction and document lifecycle unchanged.
- Folder Dashboard retains its exact previous card presentation and imports. No theme.py or rich_text_support.py changes.
- Add a current-edition source-preservation and Dashboard-only appearance gate; all historical QA, notes and fingerprints unchanged.
- GUI and AppImage rendering still requires live Fedora KDE verification.

---

# MaqaronyDesk 1.0.0-x13.4 — Theme module naming alignment (20 October 2026)

- Derived directly from MaqaronyDesk 1.0.0-x13.3. The existing `widgets/markopad_theme.py` is relocated as `widgets/theme.py` with identical file bytes.
- Only direct theme-module imports, current release identity, active QA and packaging metadata are adjusted. Palette colours, System/Light/Dark choices, settings, editor behaviour and file safety are unchanged.
- `rich_text_support.py`, standalone Pads, Plus sources, and archived QA/release records remain untouched.
- Live Fedora KDE/PyQt6 and AppImage testing is still required.

---

# MaqaronyDesk 1.0.0-x13.3 — Help and Quick Tour extraction (19 October 2026)

- Direct successor of 1.0.0-x13.2; Stage 3 is limited to seven Help / Quick Tour MainWindow methods relocated unchanged into `widgets/window_parts/help_actions.py`.
- Retains original wizard wording and pages, Quick Tour preferences and nonmodal lifecycle, keyboard-shortcut catalogue, bundled documentation, GitHub/Issues links and About dialog.
- No new features or behavioural adjustments. Historical QA, method fingerprints, checklist and previous release documentation remain unmodified below this entry.
- Static and headless QA cannot replace a live Fedora KDE/PyQt6 or AppImage run.

---

# MaqaronyDesk 1.0.0-x13.2 — Layout Controls mixin extraction (19 October 2026)

- Derived directly from 1.0.0-x13.1; extracted thirteen existing layout-control methods into `LayoutControlsMixin` without changing their bodies.
- MainWindow retains shell widget/QAction ownership, existing signal routing and persistent configuration. Focused Mode preserves temporary, non-persistent presentation changes.
- Added x13.2 frozen-source and headless tests; no historical records modified. Runtime Qt/AppImage validation on Fedora KDE remains outstanding.

---

# MaqaronyDesk 1.0.0-x13.1 — Navigation History mixin extraction (19 October 2026)

- Derived exclusively from x13.0; relocated six unchanged Back/navigation-history methods into `NavigationHistoryMixin` under `widgets/window_parts/navigation_history.py`.
- `eventFilter()`, state initialisation, QWidget/QAction ownership, workspace/path checks and existing tab implementation remain unchanged.
- New x13.1 source-preservation and headless navigation tests; historical records retained exactly. Runtime Qt and AppImage testing on Fedora KDE remain outstanding.

---

# MaqaronyDesk 1.0.0-x13.0 — Document Tabs mixin extraction (19 October 2026)

- Derived directly from MaqaronyDesk 1.0.0-x12.1; begins the approved Stage 3 MainWindow decomposition.
- Moved exactly 25 existing Document Tabs methods and three tab-token class constants into `widgets/window_parts/document_tabs.py` as `DocumentTabsMixin`. MainWindow retains QTabBar creation and signal connections; original tab behaviour, persisted keys and namespace tokens are unchanged.
- Added frozen x12.1 source preservation and active x13.0 extraction checks. Historical release records, old QA scripts and reference files remain unmodified.
- No navigation-history, layout-controls, Help/Quick Tour, editor, workspace/file safety, controller or service changes; live PyQt6 and AppImage checks still require Fedora KDE testing.

---

# MaqaronyDesk 1.0.0-x12.1 — Workspace and dialog folder convergence (19 October 2026)

- Derived directly from MaqaronyDesk 1.0.0-x12.0. Relocated four workspace UI modules to `widgets/workspace/` and six dialog modules to `widgets/dialogs/`. No editor, controller, service, document lifecycle or file-safety changes.
- Updated affected imports, and only the three moved dashboard asset lookup anchors. Preserved original icon assets, actions, presentation and dialogs.
- Added the x12.1 baseline-frozen preservation gate and active source checks; all historical QA scripts, archives and earlier changelog/release-note text remain byte-for-byte intact.
- Source/static checks do not constitute live PyQt6, Fedora KDE or AppImage verification.

---

# MaqaronyDesk 1.0.0-x12.0 — Editor folder convergence (19 October 2026)

- Derived exclusively from MaqaronyDesk 1.0.0-x11.1. Moved six existing editor modules unchanged apart from import routing into `widgets/mwpyn/` (`editor_source`, `editor_preview`, `editor_widgets`, `editor_formatting`, `editor_insertion`, `editor_search_view`), following the MaqaronyPad directory convention.
- Updated only affected production import statements. Retained Desk-specific `CodeEditor`, `EditorPage`, Desk lifecycle and printing, MainWindow, controllers, file safety, workspace monitoring and configuration unchanged. No Pad code copied or runtime dependency added.
- Added a new x12.0 exact-AST/source-preservation gate using the retained x11.0/x10 lineage reference; kept historical x11.1 and earlier gates/fixtures unmodified. Updated release metadata, packaging examples and current documentation; source manifest regenerated.
- GUI behaviour and AppImage packaging require target Linux/PyQt6 validation; source/static QA does not replace host-side testing.

---

# MaqaronyDesk 1.0.0-x11.1 — Corrective release

- Restored authentic Marko Plus 0.4.17 history from the original source rather than retrospectively relabelling that release.
- Archived the exact unmodified x10 historical records for provenance and added source-hash regression checks.
- Updated current build guidance, AppStream description and helper-script executable permissions.
- Application runtime/editor behavior is unchanged; Windows configuration work remains outside this release.

---

# MaqaronyDesk 1.0.0-x11.0 — Rebrand release

- Direct successor to MepyNamu 1.0.0-x10.0; public and technical identities updated under Contract v1.1, excluding Mwpyn.
- Existing editor, preview, document safety and workspace behavior retained. Historic release notes below are preserved verbatim.
- Fedora GUI and finished AppImage require host-side validation.

---

# MepyNamu 1.0.0-x10.0 — Embedded editor file-lifecycle extraction

- Derived directly from `1.0.0-x8.0` (x9 was standalone-only). Moved 24 original `EditorPage` lifecycle methods verbatim to `widgets/editor_lifecycle.py` using `EditorLifecycleMixin`.
- Existing file services, workspace controllers, repository, watcher and Save/Save As / external-change ownership remain unchanged.
- Updated required exact source-identity QA and source-location checks. GitHub root README updated only for the release version.
- No new features, dialog migration, constants extraction, folder migration, or shared runtime.
- Live PyQt6 GUI and AppImage/Windows builds not run in this environment.

---

# MepyNamu 1.0.0-x8.0 — Commands, icons and appearance extraction

- Derived exclusively from MepyNamu 1.0.0-x6.1; standalone-only x7 was skipped.
- Relocated 11 unchanged workspace command/icon/appearance methods and 7 unchanged editor-page menu/appearance methods into their dedicated mixins.
- Preserved the original workspace-editor boundaries, shortcuts, themes, document workflows, dialogs and editor behaviour.
- Added x8 exact-source identity and inheritance checks, retaining the x1–x6.1 regression gates.
- The public GitHub root README was changed only for version references; no new functionality or unrelated migrations.

---

# MepyNamu 1.0.0-x6.1 — Corrective release

- Restored executable permissions (`chmod 755`) to the existing portable `main.py`, preserving its contents and shebang.
- Direct continuation of 1.0.0-x6.0, retaining all x1–x6 editor extraction work, the restored GitHub root README, and existing file-safety contracts.
- Version/packaging metadata and regression checks synchronized; no new features, dialog extraction, or unrelated changes.

---

# MepyNamu 1.0.0-x6.0 — Preferences and New Document Defaults stage

- Branched directly from the issued 1.0.0-x5.0 source without changes to unrelated application or editor behaviour.
- Relocated 1 existing editor preference method(s), with unchanged source text; retained each application's current configuration service and paths. No independent new-document-defaults method existed to extract in the inspected sources.
- Restored the public repository-root README directly from the original 0.5.0 source, changing only necessary current-version references. Experimental release notes remain in internal documentation only.
- Added x6 source-identity, README-integrity and packaging regression checks; prior x1–x5 identity and file-safety checks retained.
- No dialog extraction, app-constants extraction, editor-folder reorganisation, shared library or new functionality.

---

# MepyNamu 1.0.0-x5.0 — Printing, PDF and Document Information

- Branches directly from **1.0.0-x4.0**, maintaining its complete source and configuration lineage.
- Original printing/PDF and Properties method bodies relocated text-identically into dedicated x5 mixins, keeping MepyNamu's application-specific editor/workspace ownership.
- Completes the approved x4 filename convergence by removing obsolete import-only source-editor and preview module shims; canonical `editor_source.py` and `editor_preview.py` stay unchanged.
- Retains original dialog layout/text, commands, shortcuts, source-versus-preview behaviour, security and file-lifecycle semantics; no dialog migration, app-constants migration or editor-folder restructuring.
- New x5 source-fingerprint gate added to the retained full release QA. Runtime Qt and AppImage/Windows builds are not validated in this source-only environment.

---

# MepyNamu 1.0.0-x4.0 — Search and view extraction with filename convergence

- Derived exclusively from 1.0.0-x3.0.
- Original editor source search/decorations/view methods relocated unchanged to `widgets/editor_search_view.py`.
- Original EditorPage Find/Replace/view methods relocated unchanged to `widgets/editor_page_search_view.py`.
- Canonical `widgets/editor_source.py` and `widgets/editor_preview.py` with original import names preserved via compatibility shims.
- Preview implementation byte-for-byte identical. No dialog, constants, editor-folder or shared-foundation migration.

---

# MepyNamu 1.0.0-x3.0 — insertion and clipboard extraction

- Derived solely from MepyNamu 1.0.0-x2.0.
- Relocated 16 unchanged source-editor input, guarded clipboard, drag-and-drop and Markdown insertion methods into `widgets/editor_insertion.py` as `EditorInsertionMixin`.
- The existing MepySivu source editor and workspace services retain all responsibilities and original safeguards; all method definition texts preserved, including existing product messages.
- x3 gate verifies the full original 57-method source-editor inventory alongside x1 and x2 gates.
- No source/preview module rename (reserved for x4), dialogs, constants, folders, workspace infrastructure or new features.

---

# MepyNamu 1.0.0-x2.0 — editor formatting extraction

- Derived strictly from **1.0.0-x1.0**, preserving separate standalone/workspace responsibilities.
- Relocated 13 existing Markdown source-editor formatting methods into `widgets/editor_formatting.py` as `EditorFormattingMixin`, without editing their definition text.
- The Markdown source editor continues to expose the same class and commands through inheritance. No Markdown preview, insertion, clipboard, file lifecycle, preferences or dialog changes.
- An exact-text method fingerprint gate verifies all 57 baseline source-editor methods, including the 44 retained in the original class.
- Updated active build/source-package contracts and retained historical release records.
- File-name alignment to `editor_source.py` and `editor_preview.py` is reserved for x4.0; no module renames now.

---

# MepyNamu 1.0.0-x1.0

Stage x1.0 of the strictly behaviour-preserving editor extraction programme. Moved the existing Markdown highlighter and line-number support definitions into `widgets/editor_widgets.py` with their method bodies unchanged. Kept original source-editor imports and all workspace behaviour. No dialogs, app constants, editor folders or new features.

---

# Marko Plus 0.4.17

Marko Plus 0.4.17 is deliberately limited to correcting the missing visible shortcut on the Toggle Comment AppMenu action from 0.4.16.

- **Edit → Toggle Comment** now carries the real `Ctrl+/` QAction shortcut, matching Markopad, so the keybind is visible in the AppMenu.
- The Keyboard Shortcuts dialog now discovers Toggle Comment from that live AppMenu QAction rather than adding a separate menu-less exception.
- Toggle Comment remains in the same Edit position: after Delete and before Duplicate Line/Selection.
- Toggle Comment behavior, source-editor implementation, Ribbon placement, File Ribbon ordering, More Actions ordering, and all unrelated functionality are unchanged.
