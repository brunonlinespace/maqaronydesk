# MepyNamu Architecture

## Startup

1. `main.py` delegates to the dependency-free application entry point.
2. `RuntimePaths` resolves source, frozen, or AppImage locations.
3. `ConfigService` safely loads user settings.
4. `ProjectRegistry` resolves the active registered Workspace.
5. `MainWindow` creates the persistent shell and paints immediately.
6. `FilesystemWatcher` runs one cancellable `ModuleScanner` traversal.
7. The resulting snapshot updates documents, folders, and watched paths.

## Data and state

- `Module` stores metadata and editor state for one Markdown document.
- `ModuleRepository` owns canonical document objects and emits incremental
  add/remove/change/path signals.
- `ModuleStateStore` keeps lazy Qt widgets outside the pure data model.
- `ProjectRegistry` stores Workspace folder records and small per-Workspace UI
  state. Inactive Workspaces are not scanned.

`Module` is the inherited generic class name; it does not imply executable or
language-runtime behavior.

## Services

- `RuntimePaths`: resources, configuration, and writable Workspace defaults.
- `ConfigService`: bounded JSON reading and atomic replacement.
- `ModuleScanner`: iterative Markdown discovery with ignore rules and
  cancellation.
- `FilesystemWatcher`: threaded scans, change debouncing, and safe shutdown.
- `DesktopLauncher`: sanitized host opening for files, folders, editors, and
  web links.
- `file_io`: stable identity checks, bounded reads, race detection, and atomic
  save helpers.

MepyNamu has no interpreter, script runner, terminal-session supervisor, or
executable-permission subsystem.

## Controllers and widgets

- `EditorManager` owns the workspace Dashboard, folder dashboards, and lazy
  editor pages.
- `MainWindow` owns application QActions; `ShellRibbon` owns their persistent
  Marko command-tab/toolbar presentation, collapse lifecycle, and command-tab
  cycling. The 0.0.9 Marko presentation remains authoritative.
- `MainWindow` also owns the temporary **Focused Mode** state snapshot. Focused
  Mode hides surrounding shell surfaces and collapses `ShellRibbon` through its
  shared non-persisting API, then restores the captured state exactly.
- `FileActionsController` owns safe document/folder mutation and import
  conflict handling.
- `NavigationWidget` owns the Dashboard destination and recursive folder tree.
- `DashboardWidget` keeps separate persistent List and Grid card sets.
- `EditorPage` owns source/preview layout, search, preferences, safe load/save,
  and external-change handling.
- `CodeEditor` is the thin adapter around the protected MepySivu source editor.
- `MarkdownPreview` is the protected MepySivu preview engine.

## Protected engine boundary

The embedded `editor_source.py` and `editor_preview.py` remain
canonical MepySivu engines. MepyNamu-specific compatibility belongs in the
adapter or editor page, not in those files.

## Shutdown contract

1. Resolve unsaved documents.
2. Save window and active-Workspace state.
3. Display closing feedback.
4. Cancel and join an active scan.
5. Exit only after those prerequisites complete.

## x4.0 editor module convergence

`widgets/editor_source.py` and `widgets/editor_preview.py` are canonical. Earlier `markopad_source_editor.py` and `markopad_preview.py` names remain import-only compatibility shims. Existing source-editor view/decorations are in `widgets/editor_search_view.py`, and the original EditorPage search/replace/view controls are in `widgets/editor_page_search_view.py`. Workspace services and document lifecycle remain unchanged.


## MaqaronyDesk x12.0 editor-directory organisation

The six canonical Markdown source/preview engine modules are now located in
`maqarony_desk/widgets/mwpyn/`: `editor_source.py`, `editor_preview.py`,
`editor_widgets.py`, `editor_formatting.py`, `editor_insertion.py`, and
`editor_search_view.py`. Earlier references above to the flat `widgets/`
locations describe the historical x4–x11 structure, not the current layout.

Desk-specific `widgets/code_editor.py` remains the embedded engine adapter;
`widgets/editor_page.py` and its page lifecycle and presentation mixins remain
Desk-owned. No editor methods, state models or workspace services have moved.
The MaqaronyPad app remains a separate product and source package.


## MaqaronyDesk x12.1 workspace/widget organisation

The four existing workspace presentation modules are in `widgets/workspace/`:
`navigation.py`, `dashboard.py`, `dashboard_card.py`, and `folder_dashboard.py`.
The six application dialogs are in `widgets/dialogs/`. Their previously
flat paths, described above, are historical references. MainWindow,
ShellRibbon, EditorPage, editor packages, controllers, models, and services
retain their previous ownership. No command, state, signal, file-safety,
or workspace lifecycle semantics were changed.


## MaqaronyDesk x13.0 Document Tabs extraction

The existing 25 document-tab methods and three navigation-tab token constants
now belong to `widgets/window_parts/document_tabs.py` (`DocumentTabsMixin`).
`MainWindow` continues to construct/own the QTabBar, editor manager,
QActions and signal connections. The mixin operates on the existing window
instance; editor/document lifecycles, persistence keys, close semantics and
historical `marko-plus://navigation/` tokens are unchanged.
Navigation history, layout controls and Help/Quick Tour remain in MainWindow
for their separately scoped later Stage 3 releases.


## MaqaronyDesk x13.1 Navigation History extraction

`widgets/window_parts/navigation_history.py` owns the six existing navigation-history
methods through `NavigationHistoryMixin`. MainWindow continues to initialise the
history state, wire the navigation controls, and own `eventFilter()`; document
tabs, focus handling and workspace/file lifecycle remain at their established
boundaries. No new controller, signals or persisted keys were introduced.

## 1.0.0-x13.2 layout-controls extraction

The layout visibility/placement operations now reside in `widgets/window_parts/layout_controls.py` as `LayoutControlsMixin`. MainWindow continues to own splitter, sidebar, status, editor pages, Ribbon, actions, signals, settings and Focused Mode state. No behaviour change was intended.


## 1.0.0-x13.3 MainWindow Help action extraction

The seven existing Help / Quick Tour methods now reside in
`widgets/window_parts/help_actions.py` as `HelpActionsMixin`. MainWindow
still constructs the Help QActions and menus, owns wizard/dialog state and
connects Qt signals. The original method bodies and all behavioural
contracts are retained. This is organisational work only.

## 1.0.0-x13.4 — Theme module naming

The standalone markopad_theme.py palette helper was moved byte-for-byte to `widgets/theme.py`; existing theme importers were updated. Theme behaviour, editor ownership, settings and workspace/file-safety services are unchanged.
