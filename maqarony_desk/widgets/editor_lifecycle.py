# Existing MaqaronyDesk editor-page file-lifecycle methods, moved unchanged.
from __future__ import annotations
import codecs
import locale
import os
import tempfile
from pathlib import Path
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QInputDialog, QMessageBox
from maqarony_desk.legacy_ricopad import strip_legacy_envelope
from maqarony_desk.models.module import Module
from maqarony_desk.services.file_io import (FileSnapshot, FileStateChangedError, FileTooLargeError,
    UnsupportedFileError, current_file_state, fsync_directory, install_new_file_from_temp,
    read_regular_file, snapshot_from_payload, validated_symlink_target)


class EditorLifecycleMixin:

    def _decode_source(self, data: bytes) -> tuple[str, str, bytes]:
        """Decode a Markdown document with BOM and safe fallback handling."""
        bom_map = (
            (codecs.BOM_UTF32_LE, "utf-32-le"),
            (codecs.BOM_UTF32_BE, "utf-32-be"),
            (codecs.BOM_UTF8, "utf-8"),
            (codecs.BOM_UTF16_LE, "utf-16-le"),
            (codecs.BOM_UTF16_BE, "utf-16-be"),
        )
        for bom, encoding in bom_map:
            if data.startswith(bom):
                return data[len(bom):].decode(encoding, errors="strict"), encoding, bom

        try:
            return data.decode("utf-8", errors="strict"), "utf-8", b""
        except UnicodeDecodeError:
            system_encoding = locale.getpreferredencoding(False) or "utf-8"
            choices = [
                "Windows-1252",
                "ISO-8859-1",
                "UTF-16 LE",
                "UTF-16 BE",
                f"System encoding ({system_encoding})",
            ]
            selected, accepted = QInputDialog.getItem(
                self,
                "Choose Source Encoding",
                f"{self.module.filename} is not valid UTF-8 or a recognised text encoding.\n\nOpen using:",
                choices,
                0,
                False,
            )
            if not accepted:
                raise UnicodeDecodeError("utf-8", data, 0, min(1, len(data)), "opening cancelled")
            encoding = {
                "Windows-1252": "cp1252",
                "ISO-8859-1": "iso-8859-1",
                "UTF-16 LE": "utf-16-le",
                "UTF-16 BE": "utf-16-be",
                f"System encoding ({system_encoding})": system_encoding,
            }[selected]
            return data.decode(encoding, errors="strict"), encoding, b""

    @staticmethod
    def _looks_binary_text(text: str) -> bool:
        if "\x00" in text:
            return True
        if not text:
            return False
        controls = sum(
            1 for char in text
            if ord(char) < 32 and char not in "\t\n\r\f\b"
        )
        return controls / len(text) > 0.02

    @staticmethod
    def _detect_newline_style(content: str) -> str:
        crlf = content.count("\r\n")
        stripped = content.replace("\r\n", "")
        cr = stripped.count("\r")
        lf = stripped.count("\n")
        if crlf >= cr and crlf >= lf and crlf:
            return "\r\n"
        if cr > lf and cr:
            return "\r"
        return "\n"

    def load_from_disk(self, *, show_errors: bool = True) -> bool:
        """Load one stable regular Markdown file with bounded decoding."""
        try:
            data, snapshot = read_regular_file(self.module.path, self.MAX_FILE_BYTES)
            text, encoding, bom = self._decode_source(data)
            if self._looks_binary_text(text):
                raise UnsupportedFileError("The file appears to contain binary control data.")
        except FileTooLargeError as error:
            if show_errors:
                QMessageBox.warning(self, "File Too Large", str(error))
            self.status_message.emit(f"Could not load {self.module.filename}: {error}")
            return False
        except UnsupportedFileError as error:
            if show_errors:
                QMessageBox.warning(self, "Unsupported File", str(error))
            self.status_message.emit(f"Could not load {self.module.filename}: {error}")
            return False
        except FileStateChangedError as error:
            if show_errors:
                QMessageBox.warning(self, "File Changed", str(error))
            self.status_message.emit(f"Could not load {self.module.filename}: {error}")
            return False
        except UnicodeDecodeError as error:
            if show_errors:
                QMessageBox.warning(self, "Encoding Error", str(error))
            self.status_message.emit(f"Could not load {self.module.filename}: {error}")
            return False
        except (OSError, MemoryError) as error:
            if show_errors:
                QMessageBox.critical(
                    self,
                    "Could Not Open File",
                    f"Could not read {self.module.filename}:\n\n{error}",
                )
            self.status_message.emit(f"Could not load {self.module.filename}: {error}")
            return False

        portable_text, legacy = strip_legacy_envelope(text)
        if legacy:
            QMessageBox.information(
                self,
                "Legacy Ricopad Markdown",
                "This file contains legacy Ricopad rich-format metadata. "
                "MaqaronyDesk will edit only the portable Markdown content. "
                "Saving removes the Ricopad metadata.",
            )
        if len(portable_text) > self.editor.MAX_DOCUMENT_CHARACTERS:
            message = "The decoded document exceeds MaqaronyDesk's editor safety limit."
            if show_errors:
                QMessageBox.warning(self, "File Too Large", message)
            self.status_message.emit(f"Could not load {self.module.filename}: {message}")
            return False
        newline = self._detect_newline_style(text)
        normalised = portable_text.replace("\r\n", "\n").replace("\r", "\n")
        self._ignore_document_signal = True
        try:
            self.editor.load_text(normalised)
            cursor = self.editor.textCursor()
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()
            self.editor.verticalScrollBar().setValue(
                self.editor.verticalScrollBar().minimum()
            )
            self.editor.document().clearUndoRedoStacks()
            self.editor.mark_clean()
        finally:
            self._ignore_document_signal = False

        self.file_encoding = encoding
        self.file_bom = bom
        self.legacy_ricopad_loaded = legacy
        self.file_newline = newline
        self.file_disk_snapshot = snapshot
        self._loaded_mtime_ns = snapshot.state.mtime_ns
        self._set_backing_state("normal")
        self.module.loaded = True
        self.module.modified = snapshot.state.mtime_ns / 1_000_000_000
        self.module.size = snapshot.state.size
        self.repository.set_dirty(self.module.path, False)
        self._refresh_header()
        self._update_cursor_position()
        self.refresh_search()
        self.preview.set_document_path(str(self.module.path))
        self.schedule_preview()
        self.status_message.emit(f"Loaded {self.module.filename}")
        return True

    def _encoded_editor_payload(self) -> bytes | None:
        content = self.editor.toPlainText()
        if self.file_newline != "\n":
            content = content.replace("\n", self.file_newline)
        try:
            payload = self.file_bom + content.encode(
                self.file_encoding, errors="strict"
            )
        except UnicodeEncodeError as error:
            QMessageBox.critical(
                self,
                "Encoding Error",
                f"The edited text cannot be represented as {self.file_encoding}:\n\n{error}",
            )
            return None
        if len(payload) > self.MAX_FILE_BYTES:
            message = (
                f"The file exceeds MaqaronyDesk's "
                f"{self.MAX_FILE_BYTES // (1024 * 1024)} MiB editor safety limit."
            )
            QMessageBox.warning(self, "Save Cancelled", message)
            self.status_message.emit(message)
            return None
        return payload

    def current_markdown_payload(self) -> bytes | None:
        """Return the live Markdown buffer using this document's encoding/newline contract."""
        return self._encoded_editor_payload()

    def save_copy_to(self, target: str | Path) -> bool:
        """Atomically write the live Markdown buffer to a distinct path."""
        destination = Path(target).expanduser().resolve(strict=False)
        payload = self._encoded_editor_payload()
        if payload is None:
            return False

        if destination.exists() or destination.is_symlink():
            response = QMessageBox.question(
                self,
                "Replace Markdown File? — MaqaronyDesk",
                f"'{destination.name}' already exists. Replace it with the "
                "current document?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return False
            try:
                expected = current_file_state(destination)
            except OSError as error:
                QMessageBox.warning(
                    self,
                    "Save As Cancelled",
                    f"MaqaronyDesk could not verify the destination:\n\n{error}",
                )
                return False
        else:
            expected = None

        temporary: Path | None = None
        descriptor: int | None = None
        try:
            parent = destination.parent
            parent.mkdir(parents=False, exist_ok=True)
            if expected is not None and current_file_state(destination) != expected:
                raise FileStateChangedError(
                    "The destination changed before MaqaronyDesk could save it."
                )
            descriptor, raw_path = tempfile.mkstemp(
                prefix=f".{destination.name}.marko-plus-",
                suffix=".tmp",
                dir=parent,
            )
            temporary = Path(raw_path)
            if expected is not None and hasattr(os, "fchmod"):
                os.fchmod(descriptor, expected.target_mode & 0o7777)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if expected is None:
                install_new_file_from_temp(temporary, destination)
                temporary = None
            else:
                if current_file_state(destination) != expected:
                    raise FileStateChangedError(
                        "The destination changed again before replacement."
                    )
                os.replace(temporary, destination)
                temporary = None
            fsync_directory(parent)
        except FileStateChangedError as error:
            QMessageBox.warning(self, "Save As Cancelled", str(error))
            return False
        except OSError as error:
            QMessageBox.critical(self, "Save As Failed", str(error))
            return False
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary is not None:
                try:
                    temporary.unlink()
                except OSError:
                    pass

        self.status_message.emit(
            getattr(self, "_save_version_status_override", None)
            or f"Saved as {destination.name}"
        )
        return True

    def save_as_file(self, target: str | Path) -> bool:
        """Save to a new managed path and keep this live EditorPage."""
        destination = Path(target).expanduser().resolve(strict=False)
        old_path = self.module.path.resolve(strict=False)
        if destination == old_path:
            return self.save_to_disk()
        if not self.save_copy_to(destination):
            return False

        try:
            _payload, snapshot = read_regular_file(destination, self.MAX_FILE_BYTES)
        except OSError:
            self.file_disk_snapshot = None
            self._loaded_mtime_ns = None
        else:
            self.file_disk_snapshot = snapshot
            self._loaded_mtime_ns = snapshot.state.mtime_ns

        self._ignore_document_signal = True
        try:
            self.editor.mark_clean()
        finally:
            self._ignore_document_signal = False

        self.legacy_ricopad_loaded = False
        self._set_backing_state("normal")
        self.path_changed.emit(self, old_path, destination)
        self.preview.set_document_path(str(destination))
        self.schedule_preview()
        self._refresh_header()
        self.saved.emit(self.module)
        return True

    def save_to_disk(self) -> bool:
        """Safely save while preserving encoding, newline style and file mode."""
        expected = self.file_disk_snapshot
        if expected is not None:
            action = self._external_change_action()
            if action == "reload":
                self.load_from_disk(show_errors=True)
                return False
            if action == "save_version_as":
                return self._save_editor_version_as()
            if action == "handled_success":
                return True
            if action != "overwrite":
                return False

            # Explicit Overwrite is the only conflict decision allowed to replace
            # the changed disk copy. Refresh the expected snapshot at that point
            # so the existing MaqaronyDesk atomic-save race guards still protect
            # against another change before replacement.
            try:
                _disk_data, expected = read_regular_file(
                    self.module.path, self.MAX_FILE_BYTES
                )
            except FileNotFoundError:
                expected = None
            except OSError as error:
                QMessageBox.warning(
                    self,
                    "File Check Failed",
                    f"MaqaronyDesk could not verify the file before saving:\n\n{error}",
                )
                return False

        payload = self._encoded_editor_payload()
        if payload is None:
            return False

        temporary: Path | None = None
        descriptor: int | None = None
        try:
            if expected is None:
                if self.module.path.exists() or self.module.path.is_symlink():
                    raise FileStateChangedError(
                        "A file appeared at the save location. Saving was cancelled."
                    )
                write_path = self.module.path
                existing_mode = 0o666
            else:
                if current_file_state(self.module.path) != expected.state:
                    raise FileStateChangedError(
                        "The file changed again before MaqaronyDesk could save it."
                    )
                write_path = (
                    validated_symlink_target(self.module.path, expected.state)
                    if expected.state.is_symlink
                    else self.module.path
                )
                existing_mode = expected.state.target_mode & 0o7777

            parent = write_path.parent
            descriptor, raw_path = tempfile.mkstemp(
                prefix=f".{write_path.name}.marko-plus-",
                suffix=".tmp",
                dir=parent,
            )
            temporary = Path(raw_path)
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, existing_mode)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            if expected is None:
                install_new_file_from_temp(temporary, write_path)
                temporary = None
            else:
                if current_file_state(self.module.path) != expected.state:
                    raise FileStateChangedError(
                        "The file changed again before MaqaronyDesk could replace it."
                    )
                if expected.state.is_symlink and validated_symlink_target(
                    self.module.path, expected.state
                ) != write_path:
                    raise FileStateChangedError(
                        "The symbolic-link target changed before replacement."
                    )
                os.replace(temporary, write_path)
                temporary = None
            fsync_directory(parent)
        except FileStateChangedError as error:
            QMessageBox.warning(self, "Save Cancelled", str(error))
            return False
        except OSError as error:
            QMessageBox.critical(self, "Save Failed", str(error))
            self.status_message.emit(f"Could not save {self.module.filename}: {error}")
            return False
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary is not None:
                try:
                    temporary.unlink()
                except OSError:
                    pass

        try:
            snapshot = snapshot_from_payload(self.module.path, payload)
            stat_result = self.module.path.stat()
            self.file_disk_snapshot = snapshot
            self._loaded_mtime_ns = snapshot.state.mtime_ns
            self.module.modified = stat_result.st_mtime
            self.module.size = stat_result.st_size
        except OSError:
            self.file_disk_snapshot = None
            self._loaded_mtime_ns = None

        self._ignore_document_signal = True
        try:
            self.editor.mark_clean()
        finally:
            self._ignore_document_signal = False

        self.legacy_ricopad_loaded = False
        self._set_backing_state("normal")
        self.repository.set_dirty(self.module.path, False)
        self.repository.module_changed.emit(self.module)
        self._refresh_header()
        self.saved.emit(self.module)
        self.status_message.emit(f"Saved {self.module.filename}")
        return True

    def confirm_reload(self) -> None:
        if self.editor.is_modified:
            response = QMessageBox.question(
                self,
                "Discard Changes",
                "Discard all unsaved changes and reload this file from disk?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return
        self.load_from_disk()

    @property
    def is_modified(self) -> bool:
        return bool(self.editor.is_modified)

    @property
    def backing_state(self) -> str:
        return self._backing_state

    def can_close(self) -> bool:
        """Ask whether an unsaved or backing-at-risk page may be closed."""
        if self._backing_state == "missing":
            return self._confirm_close_missing_backing()
        if not self.editor.is_modified:
            return True

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Unsaved Changes")
        box.setText(f"Save changes to {self.module.filename}?")
        save = box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is save:
            return self.save_to_disk()
        if clicked is discard:
            return True
        # Cancel, closing the dialog via its title-bar button, or any unknown
        # result must preserve the unsaved editor.
        return False

    def _confirm_close_missing_backing(self) -> bool:
        """Protect a clean or dirty live copy whose original pathname vanished."""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Backing File Missing")
        dialog.setText(
            f"{self.module.filename} is no longer available at its original path."
        )
        dialog.setInformativeText(
            "This open editor may be the only remaining copy. Save Version As "
            "preserves it at a new path. Recreate Original enters the protected "
            "Save flow, where Overwrite is still an explicit confirmation."
        )
        save_version = dialog.addButton(
            "Save Version As…", QMessageBox.ButtonRole.AcceptRole
        )
        recreate = dialog.addButton(
            "Recreate Original…", QMessageBox.ButtonRole.ActionRole
        )
        close_without = dialog.addButton(
            "Close Without Saving", QMessageBox.ButtonRole.DestructiveRole
        )
        cancel = dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.setDefaultButton(save_version)
        dialog.setEscapeButton(cancel)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is save_version:
            return self._save_editor_version_as()
        if clicked is recreate:
            return self.save_to_disk()
        if clicked is close_without:
            return True
        return False

    def _on_modification_changed(self, modified: bool) -> None:
        if self._ignore_document_signal:
            return
        self.repository.set_dirty(self.module.path, modified)
        self._refresh_header()

    def _on_module_path_changed(self, changed: Module, _old_path: Path) -> None:
        if changed is not self.module:
            return
        self._refresh_header()
        self.preview.set_document_path(str(self.module.path))
        self.schedule_preview()
        try:
            current_state = current_file_state(self.module.path)
            self._loaded_mtime_ns = current_state.mtime_ns
            if self.file_disk_snapshot is not None:
                self.file_disk_snapshot = FileSnapshot(
                    state=current_state,
                    digest=self.file_disk_snapshot.digest,
                )
        except OSError:
            self._loaded_mtime_ns = None

    def _set_backing_state(self, state: str) -> None:
        """Update the persistent live-document backing-path state."""
        if state not in {"normal", "changed", "missing"}:
            raise ValueError(f"Unknown backing state: {state}")
        self._backing_state = state
        self._external_change_pending = state != "normal"
        if state == "normal":
            self.reload_external_button.setEnabled(True)
            self.external_label.setText("This file changed on disk after it was opened.")
            self.external_banner.hide()
            # Resolve only this backing-file warning; preserve unrelated
            # critical messages regardless of wording.
            self.editor_status.clearMessage(warning_id="backing_file")
            return
        if state == "missing":
            self.external_label.setText(
                "This file is no longer available at its original disk path. "
                "Save Version As preserves the live document; Reload is unavailable."
            )
            self.reload_external_button.setEnabled(False)
        else:
            self.external_label.setText("This file changed on disk after it was opened.")
            self.reload_external_button.setEnabled(True)
        self.external_banner.show()
        self._refresh_header()

    def handle_backing_path_event(self, *, notify: bool = False) -> None:
        """Resolve a targeted monitor event using the exact Markdown byte snapshot."""
        loaded = self.file_disk_snapshot
        if loaded is None:
            return
        previous_state = self._backing_state
        current = self._current_disk_snapshot()
        if current is None:
            self._set_backing_state("missing")
        elif current.digest == loaded.digest:
            self._loaded_mtime_ns = current.state.mtime_ns
            self.file_disk_snapshot = current
            self._set_backing_state("normal")
        else:
            self._set_backing_state("changed")
        if notify and previous_state != self._backing_state:
            if self._backing_state == "missing":
                self.show_editor_status(
                    "Backing file missing; the live MaqaronyDesk document remains protected.",
                    4000, warning_id="backing_file",
                )
            elif self._backing_state == "changed":
                self.show_editor_status(
                    "File changed outside MaqaronyDesk.", 4000,
                    warning_id="backing_file",
                )

    def _current_disk_snapshot(self) -> FileSnapshot | None:
        """Return the exact-byte snapshot for the managed disk copy."""
        try:
            _payload, snapshot = read_regular_file(
                self.module.path, self.MAX_FILE_BYTES
            )
        except OSError:
            return None
        return snapshot

    def _has_external_change(self) -> bool:
        loaded = self.file_disk_snapshot
        if loaded is None:
            return False
        current = self._current_disk_snapshot()
        return current is None or current.digest != loaded.digest

    def _external_change_action(self) -> str:
        """Own the managed Plus conflict decision for every Save route."""
        if not self._has_external_change():
            self._set_backing_state("normal")
            return "overwrite"

        current_snapshot = self._current_disk_snapshot()
        self._set_backing_state(
            "missing" if current_snapshot is None else "changed"
        )

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("File Changed on Disk")
        if current_snapshot is None:
            dialog.setText(
                "This file is no longer available at its original disk path."
            )
            dialog.setInformativeText(
                "Save Version As preserves the current MaqaronyDesk document at a "
                "new path. Overwrite explicitly recreates the original path. "
                "Reload is unavailable until a disk copy exists again."
            )
        else:
            dialog.setText(
                "This file has changed on disk since MaqaronyDesk opened or saved it."
            )
            dialog.setInformativeText(
                "Choose Reload to discard the current MaqaronyDesk edits and use the "
                "disk copy, Save Version As to preserve both versions, or Overwrite "
                "to explicitly replace the changed disk copy with the current document."
            )
        reload_button = dialog.addButton("Reload", QMessageBox.ButtonRole.ActionRole)
        reload_button.setEnabled(current_snapshot is not None)
        save_version_button = dialog.addButton(
            "Save Version As…", QMessageBox.ButtonRole.ActionRole
        )
        overwrite_button = dialog.addButton(
            "Overwrite", QMessageBox.ButtonRole.DestructiveRole
        )
        cancel_button = dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is reload_button:
            self._reload_external_change()
            return "cancel"
        if clicked is save_version_button:
            return "handled_success" if self._save_editor_version_as() else "cancel"
        if clicked is overwrite_button:
            return "overwrite"
        return "cancel"

    def _on_repository_module_changed(self, changed: Module) -> None:
        """Surface watcher-detected external changes for this open document.

        Scanner metadata is only the notification trigger. The decision is made
        from the exact file digest, so timestamp-only touches do not produce a
        false warning.
        """
        if changed is not self.module and changed.path != self.module.path:
            return

        self.handle_backing_path_event(notify=True)

    def _reload_external_change(self) -> None:
        if self.editor.is_modified:
            response = QMessageBox.question(
                self,
                "Discard Editor Changes",
                "Reloading will discard your unsaved editor changes. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return
        self.load_from_disk()

    def _save_editor_version_as(self) -> bool:
        """Preserve the Marko editor version without touching the changed disk copy."""
        handler = getattr(self.window(), "_save_external_change_version_as", None)
        if not callable(handler):
            return False
        return bool(handler(self))
