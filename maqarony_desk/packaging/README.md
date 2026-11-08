# MaqaronyDesk Packaging

## Fedora 43/44 native x86_64/aarch64 AppImage

```bash
./maqarony_desk/packaging/fedora/install-build-deps.sh
./maqarony_desk/packaging/fedora/build-appimage.sh
```

Run the build as your normal user. The dependency installer uses `sudo`
internally; do not invoke `build-appimage.sh` with `sudo`.

Expected artifacts (x86_64; aarch64 builds use `aarch64`):

```text
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.AppImage
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.AppImage.sha256
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.build-info.txt
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.build-python-lock.txt
```

Test an artifact with:

```bash
./maqarony_desk/packaging/fedora/test-appimage.sh maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.AppImage
```

The build uses a clean virtual environment and pinned PyInstaller and
PyInstaller-hooks versions from `packaging/pyinstaller/build-requirements.txt`. Runtime PyQt6 constraints are
in `maqarony_desk/requirements.txt`.

Read `BUILDING.md` before creating a public release. Build-host desktop
integration must not be allowed to become an undeclared application dependency.

The shared Fedora scripts recognize releases 43 and 44. The `fedora43` and
`fedora44` directories contain compatibility wrappers only.

The source release check runs before creation of the build virtual environment.
Generated build areas and ordinary local Python caches are excluded from
working-tree hygiene failures. Cache files still fail validation if they are
actually tracked by Git.
