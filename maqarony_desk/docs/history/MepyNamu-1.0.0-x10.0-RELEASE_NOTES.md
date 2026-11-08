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

# MepyNamu 0.5.0

MepyNamu 0.5.0 is deliberately limited to correcting the missing visible shortcut on the Toggle Comment AppMenu action from 0.4.16.

- **Edit → Toggle Comment** now carries the real `Ctrl+/` QAction shortcut, matching MepySivu, so the keybind is visible in the AppMenu.
- The Keyboard Shortcuts dialog now discovers Toggle Comment from that live AppMenu QAction rather than adding a separate menu-less exception.
- Toggle Comment remains in the same Edit position: after Delete and before Duplicate Line/Selection.
- Toggle Comment behavior, source-editor implementation, Ribbon placement, File Ribbon ordering, More Actions ordering, and all unrelated functionality are unchanged.
