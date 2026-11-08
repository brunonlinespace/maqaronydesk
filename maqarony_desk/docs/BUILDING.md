# Building MaqaronyDesk

## Source environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r maqarony_desk/requirements.txt
python main.py
```

## Static validation

```bash
python -m maqarony_desk.qa.release_check
```

The release check does not import PyQt6, so it can run before the build
environment is created.

## Fedora 43/44 AppImage

```bash
./maqarony_desk/packaging/fedora/install-build-deps.sh
./maqarony_desk/packaging/fedora/build-appimage.sh
```

Run the builder as the normal desktop user. The dependency helper invokes
`sudo dnf`; do not invoke the builder itself with `sudo`. Controlled root-based
CI containers may explicitly set `MAQARONYDESK_ALLOW_ROOT_BUILD=1`.

Expected output (x86_64; aarch64 builds use `aarch64`):

```text
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.AppImage
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.AppImage.sha256
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.build-info.txt
maqarony_desk/dist/MaqaronyDesk-1.0.0-x86_64.build-python-lock.txt
```

The builder validates source identity and provenance, creates an isolated
virtual environment, builds a PyInstaller one-folder bundle, assembles and
validates the AppDir, then emits the AppImage and checksums.

Test the identical artifact on the intended XFCE, Plasma, and Wayland targets.
