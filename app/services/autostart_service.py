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
        if metadata is None:
            return False
        return self._matches_expected_shortcut(metadata)

    def enable(self) -> None:
        if not self.is_supported():
            raise AutostartError("Autostart is supported on Windows only.")

        self._startup_dir.mkdir(parents=True, exist_ok=True)
        self._create_shortcut()
        self._cleanup_duplicate_shortcuts()

        if not self.is_enabled():
            raise AutostartError("Autostart shortcut was created but verification failed.")
        LOGGER.info("Autostart enabled")

    def disable(self) -> None:
        if not self.is_supported():
            return

        if self._shortcut_path.exists():
            self._shortcut_path.unlink()

        self._cleanup_duplicate_shortcuts(remove_all_matching=True)
        LOGGER.info("Autostart disabled")

    def _cleanup_duplicate_shortcuts(self, remove_all_matching: bool = False) -> None:
        if not self._startup_dir.exists():
            return

        for candidate in self._startup_dir.glob(f"{self.app_name}*.lnk"):
            metadata = self._read_shortcut_metadata(candidate)
            if metadata is None:
                continue

            if not self._matches_target_executable(metadata):
                continue

            is_primary = candidate == self._shortcut_path
            if is_primary and not remove_all_matching:
                continue

            if self._matches_expected_shortcut(metadata) or remove_all_matching:
                LOGGER.info("Removing duplicate startup shortcut: %s", candidate)
                candidate.unlink(missing_ok=True)

    def _matches_expected_shortcut(self, metadata: ShortcutMetadata) -> bool:
        expected_target = str(self.executable_path).lower()
        expected_args = self.startup_argument.strip().lower()
        expected_workdir = str(self.executable_path.parent).lower()

        return (
            metadata.target_path.lower() == expected_target
            and metadata.arguments.strip().lower() == expected_args
            and metadata.working_directory.lower() == expected_workdir
        )

    def _matches_target_executable(self, metadata: ShortcutMetadata) -> bool:
        return metadata.target_path.lower() == str(self.executable_path).lower()

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

    def _create_shortcut(self) -> None:
        command = self._build_create_command()
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, shell=False)
        except OSError as exc:
            LOGGER.exception("Failed to create startup shortcut")
            raise AutostartError(f"Failed to create startup shortcut: {exc}") from exc

        if result.returncode != 0:
            message = result.stderr.strip() or "Unknown PowerShell error."
            raise AutostartError(f"Failed to create startup shortcut: {message}")

    def _build_create_command(self) -> list[str]:
        startup_dir = self._escape_ps(str(self._startup_dir))
        shortcut_path = self._escape_ps(str(self._shortcut_path))
        target_path = self._escape_ps(str(self.executable_path))
        args = self._escape_ps(self.startup_argument)
        working_dir = self._escape_ps(str(self.executable_path.parent))

        script = (
            f"$startupDir='{startup_dir}';"
            f"$shortcutPath='{shortcut_path}';"
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
