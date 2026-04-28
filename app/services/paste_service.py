from __future__ import annotations

import logging
import os
import sys

from app.core.models import ClipboardItem, ClipboardItemType
from app.services.clipboard_service import ClipboardService

LOGGER = logging.getLogger(__name__)


if sys.platform == "win32":
    import win32api
    import win32con
    import win32gui
    import win32process


class PasteService:
    """Coordinates focus restore and Ctrl+V paste into the last external window."""

    def __init__(self, clipboard_service: ClipboardService) -> None:
        self._clipboard_service = clipboard_service
        self._supported = sys.platform == "win32"
        self._own_pid = os.getpid()
        self._last_foreground_window: int | None = None

    def remember_foreground_window(self) -> None:
        if not self._supported:
            self._last_foreground_window = None
            return

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            LOGGER.debug("Skipped foreground remember: no active window handle")
            return

        if not self._is_external_window(hwnd):
            LOGGER.debug("Skipped foreground remember for internal window: %s", _format_hwnd(hwnd))
            return

        self._last_foreground_window = hwnd
        LOGGER.info("Remembered foreground window: %s", _format_hwnd(hwnd))

    def paste_item(self, item: ClipboardItem) -> bool:
        LOGGER.info("Paste requested for item=%s type=%s", item.id, item.item_type.value)

        if item.item_type is not ClipboardItemType.TEXT:
            LOGGER.warning("Paste skipped for non-text item=%s type=%s", item.id, item.item_type.value)
            return False

        restored = self._clipboard_service.restore_item(item)
        if not restored:
            LOGGER.warning("Paste aborted: clipboard restore failed for item=%s", item.id)
            return False

        return self.paste_clipboard_to_previous_window()

    def paste_clipboard_to_previous_window(self) -> bool:
        if not self._supported:
            LOGGER.warning("Paste simulation unavailable on platform=%s", sys.platform)
            return False

        target_hwnd = self._last_foreground_window
        if target_hwnd is None:
            LOGGER.warning("Paste failed: no remembered foreground window")
            return False

        if not self._is_valid_target(target_hwnd):
            LOGGER.warning("Paste failed: target window is unavailable: %s", _format_hwnd(target_hwnd))
            return False

        LOGGER.info("Restore attempt for target window: %s", _format_hwnd(target_hwnd))
        if not self.restore_foreground_window():
            LOGGER.warning("Paste failed: SetForegroundWindow was denied/unsuccessful for %s", _format_hwnd(target_hwnd))
            return False

        LOGGER.info("Paste attempt started for target window: %s", _format_hwnd(target_hwnd))
        pasted = self.send_ctrl_v()
        if pasted:
            LOGGER.info("Paste success for target window: %s", _format_hwnd(target_hwnd))
        else:
            LOGGER.warning("Paste failure while sending Ctrl+V to target window: %s", _format_hwnd(target_hwnd))
        return pasted

    def restore_foreground_window(self) -> bool:
        if not self._supported:
            return False

        target_hwnd = self._last_foreground_window
        if target_hwnd is None:
            return False

        if not self._is_valid_target(target_hwnd):
            return False

        try:
            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(target_hwnd)
            win32gui.SetForegroundWindow(target_hwnd)
        except Exception:
            LOGGER.exception("Failed to restore foreground window: %s", _format_hwnd(target_hwnd))
            return False

        active_hwnd = win32gui.GetForegroundWindow()
        return active_hwnd == target_hwnd

    def send_ctrl_v(self) -> bool:
        if not self._supported:
            return False

        try:
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord("V"), 0, 0, 0)
            win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            LOGGER.exception("Failed to send Ctrl+V")
            return False

    def _is_external_window(self, hwnd: int) -> bool:
        if not self._supported:
            return False

        if not win32gui.IsWindow(hwnd):
            return False

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid != 0 and pid != self._own_pid

    def _is_valid_target(self, hwnd: int) -> bool:
        return self._supported and win32gui.IsWindow(hwnd) and self._is_external_window(hwnd)


def _format_hwnd(hwnd: int) -> str:
    return f"0x{int(hwnd):X}"
