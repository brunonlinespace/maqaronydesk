# Recovered GitHub README changes (historical archive only)

Captured from source MaqaronyDesk 1.0.0-x21.3 before restoration. This is NOT the GitHub README.
The canonical README is protected except for current-version field(s).

```diff
--- authoritative README
+++ pre-repair README 1.0.0-x21.3
@@ -1,3 +1,24 @@
+# MaqaronyDesk 1.0.0-x21.3 — Exit on File toolbar (2026-10-31)
+
+- Expose the **existing Exit QAction** as the **final command** in the File Ribbon tab, after a separator.
+- Use the already-packaged `exit.png` light/dark icons and existing Quit shortcut (`Ctrl+Q` on Linux) in its tooltip.
+- Keep AppMenu Exit, close confirmation, workspace state, icon assets and all other commands unchanged.
+- Static source check for File-tab order, action identity, icon mapping and shortcut tooltip; live PyQt6/KDE testing remains pending.
+
+---
+
+# MaqaronyDesk 1.0.0-x21.1 — Desk icon wiring correction (2026-10-31)
+
+A narrow source-only follow-up to x21.0. Open External File uses `open.png`; Dashboard-card Edit uses `file-launch.png`; Show Sidebar switches between `show-sidebar.png` (left dock) and `show-sidebar-right.png` (right dock) in the shared QAction used by Ribbon and AppMenu. Dock changes update the artwork immediately; changing theme refreshes the correct icon. Visibility check state, file actions, layouts, configuration semantics and all 288 icon PNGs remain unchanged. Live KDE/PyQt6 UI testing is outstanding.
+
+---
+
+# MaqaronyDesk 1.0.0-x21.0 — canonical toolbar icon pack (2026-10-31)
+
+Canonical 288-PNG toolbar icon replacement and five approved icon wiring targets; no legacy toolbar asset retention.
+
+---
+
 <p align="center">
   <a href="https://github.com/brunonlinespace/maqaronydesk">
     <img
@@ -14,7 +35,7 @@
 
 MaqaronyDesk is a workspace-scale Markdown editor built around the established Markdown source editor and preview engine. It adds managed workspaces, folder navigation, dashboards, persistent application settings, and the shared Plus-family document lifecycle while continuing to read and write ordinary Markdown files.
 
-Current release: **1.0.0-x18.8**
+Current release: **1.0.0-x21.0**
 
 **x15.2:** Retains x15.0 shutdown and x15.1 geometry improvements; updates Dashboard search visibility in place and avoids unnecessary card-layout rebuilding. Changes are performance-only and await KDE benchmarking.
 
```
