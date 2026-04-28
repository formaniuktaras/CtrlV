from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class AutostartError(RuntimeError):
    """Raised when autostart state cannot be updated."""


@dataclass(slots=True)
class ShortcutMetadata:
    target_path: str
    arguments: str
    working_directory: str


@dataclass(slots=True)
class AutostartService:
    """Windows per-user autostart management via Startup-folder shortcut."""

    app_name: str
    executable_path: Path
    startup_argument: str = "--startup"
    _startup_dir: Path = field(init=False, repr=False)
    _shortcut_path: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        self._shortcut_path = self._startup_dir / f"{self.app_name}.lnk"

    @property
    def startup_shortcut_path(self) -> Path:
        return self._shortcut_path

    def is_supported(self) -> bool:
        return os.name == "nt" and bool(os.environ.get("APPDATA"))

    def is_enabled(self) -> bool:
        if not self.is_supported() or not self._shortcut_path.exists():
            return False

        metadata = self._read_shortcut_metadata(self._shortcut_path)
        return metadata is not None and self._matches_expected_shortcut(metadata)

    def enable(self) -> None:
        if not self.is_supported():
            raise AutostartError("Autostart is supported on Windows only.")

        self._startup_dir.mkdir(parents=True, exist_ok=True)

        metadata = self._read_shortcut_metadata(self._shortcut_path)
        if metadata is None or not self._matches_expected_shortcut(metadata):
            self._create_shortcut(self._shortcut_path)

        self._cleanup_duplicate_shortcuts()

        if not self.is_enabled():
            raise AutostartError("Autostart shortcut was created but verification failed.")
        LOGGER.info("Autostart enabled (shortcut=%s, args=%s)", self._shortcut_path, self.startup_argument)

    def disable(self) -> None:
        if not self.is_supported():
            return

        if self._shortcut_path.exists():
            self._shortcut_path.unlink(missing_ok=True)

        self._cleanup_duplicate_shortcuts(remove_expected_duplicates=True)
        LOGGER.info("Autostart disabled")

    def _cleanup_duplicate_shortcuts(self, remove_expected_duplicates: bool = False) -> None:
        if not self._startup_dir.exists():
            return

        for candidate in self._managed_shortcut_candidates():
            if candidate == self._shortcut_path and not remove_expected_duplicates:
                continue

            metadata = self._read_shortcut_metadata(candidate)
            if metadata is None:
                continue

            if self._matches_expected_shortcut(metadata):
                LOGGER.info("Removing duplicate startup shortcut: %s", candidate)
                candidate.unlink(missing_ok=True)

    def _managed_shortcut_candidates(self) -> list[Path]:
        candidate_names = {
            f"{self.app_name}.lnk",
            f"{self.app_name} Startup.lnk",
            f"{self.app_name} Autostart.lnk",
        }
        return [self._startup_dir / name for name in candidate_names if (self._startup_dir / name).exists()]

    def _matches_expected_shortcut(self, metadata: ShortcutMetadata) -> bool:
        expected_target = self._normalize_path(self.executable_path)
        expected_args = self.startup_argument.strip().lower()
        expected_workdir = self._normalize_path(self.executable_path.parent)

        return (
            self._normalize_path(metadata.target_path) == expected_target
            and metadata.arguments.strip().lower() == expected_args
            and self._normalize_path(metadata.working_directory) == expected_workdir
        )

    def _normalize_path(self, value: str | Path) -> str:
        path = Path(value).expanduser()
        try:
            path = path.resolve(strict=False)
        except OSError:
            pass
        return str(path).lower().rstrip("\\/")

    def _read_shortcut_metadata(self, shortcut_path: Path) -> ShortcutMetadata | None:
        if not shortcut_path.exists():
            return None

        command = self._build_read_command(shortcut_path)
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, shell=False)
        except OSError as exc:
            LOGGER.exception("Failed to inspect startup shortcut")
            raise AutostartError(f"Failed to inspect startup shortcut: {exc}") from exc

        if result.returncode != 0:
            LOGGER.warning("Failed to inspect shortcut %s: %s", shortcut_path, result.stderr.strip())
            return None

        lines = [line.strip().strip('"') for line in result.stdout.splitlines()]
        if len(lines) < 3:
            return None

        return ShortcutMetadata(
            target_path=lines[0],
            arguments=lines[1],
            working_directory=lines[2],
        )

    def _create_shortcut(self, shortcut_path: Path) -> None:
        command = self._build_create_command(shortcut_path)
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, shell=False)
        except OSError as exc:
            LOGGER.exception("Failed to create startup shortcut")
            raise AutostartError(f"Failed to create startup shortcut: {exc}") from exc

        if result.returncode != 0:
            message = result.stderr.strip() or "Unknown PowerShell error."
            raise AutostartError(f"Failed to create startup shortcut: {message}")

    def _build_create_command(self, shortcut_path: Path) -> list[str]:
        shortcut_target = self._escape_ps(str(shortcut_path))
        target_path = self._escape_ps(str(self.executable_path))
        args = self._escape_ps(self.startup_argument)
        working_dir = self._escape_ps(str(self.executable_path.parent))

        script = (
            f"$shortcutPath='{shortcut_target}';"
            f"$targetPath='{target_path}';"
            f"$ws=New-Object -ComObject WScript.Shell;"
            f"$sc=$ws.CreateShortcut($shortcutPath);"
            f"$sc.TargetPath=$targetPath;"
            f"$sc.Arguments='{args}';"
            f"$sc.WorkingDirectory='{working_dir}';"
            f"$sc.IconLocation=$targetPath;"
            "$sc.Save();"
        )
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]

    def _build_read_command(self, shortcut_path: Path) -> list[str]:
        escaped = self._escape_ps(str(shortcut_path))
        script = (
            f"$shortcutPath='{escaped}';"
            "$ws=New-Object -ComObject WScript.Shell;"
            "$sc=$ws.CreateShortcut($shortcutPath);"
            "Write-Output $sc.TargetPath;"
            "Write-Output $sc.Arguments;"
            "Write-Output $sc.WorkingDirectory;"
        )
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]

    @staticmethod
    def _escape_ps(value: str) -> str:
        return value.replace("'", "''")
