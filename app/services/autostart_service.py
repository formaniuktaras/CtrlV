from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class AutostartError(RuntimeError):
    """Raised when autostart state cannot be updated."""


@dataclass(slots=True)
class AutostartService:
    """Windows per-user autostart management via Startup-folder shortcut."""

    app_name: str
    executable_path: Path
    startup_argument: str = "--startup"

    def __post_init__(self) -> None:
        self._startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        self._shortcut_path = self._startup_dir / f"{self.app_name}.lnk"

    @property
    def startup_shortcut_path(self) -> Path:
        return self._shortcut_path

    def is_supported(self) -> bool:
        return os.name == "nt" and bool(os.environ.get("APPDATA"))

    def is_enabled(self) -> bool:
        if not self.is_supported():
            return False
        if not self._shortcut_path.exists():
            return False
        return self._shortcut_points_to_executable()

    def enable(self) -> None:
        if not self.is_supported():
            raise AutostartError("Autostart is supported on Windows only.")

        self._startup_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_duplicate_shortcuts()
        self._create_shortcut()

        if not self.is_enabled():
            raise AutostartError("Autostart shortcut was created but verification failed.")

    def disable(self) -> None:
        if not self.is_supported():
            return

        if self._shortcut_path.exists():
            self._shortcut_path.unlink()

        self._cleanup_duplicate_shortcuts()

    def _cleanup_duplicate_shortcuts(self) -> None:
        if not self._startup_dir.exists():
            return

        for candidate in self._startup_dir.glob(f"{self.app_name}*.lnk"):
            if candidate == self._shortcut_path:
                continue
            if self._shortcut_target_matches(candidate):
                LOGGER.info("Removing duplicate startup shortcut: %s", candidate)
                candidate.unlink(missing_ok=True)

    def _shortcut_points_to_executable(self) -> bool:
        return self._shortcut_target_matches(self._shortcut_path)

    def _shortcut_target_matches(self, shortcut_path: Path) -> bool:
        if not shortcut_path.exists():
            return False

        command = self._build_read_command(shortcut_path)
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, shell=False)
        except OSError as exc:
            LOGGER.exception("Failed to inspect startup shortcut")
            raise AutostartError(f"Failed to inspect startup shortcut: {exc}") from exc

        if result.returncode != 0:
            LOGGER.warning("Failed to inspect shortcut %s: %s", shortcut_path, result.stderr.strip())
            return False

        target = result.stdout.strip().strip('"').lower()
        return target == str(self.executable_path).lower()

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
        )
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]

    @staticmethod
    def _escape_ps(value: str) -> str:
        return value.replace("'", "''")
