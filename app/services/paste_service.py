from __future__ import annotations

import ctypes
import logging
import os
import sys
import time
from dataclasses import dataclass

from app.core.models import ClipboardItem, ClipboardItemType
from app.services.clipboard_service import ClipboardService

LOGGER = logging.getLogger(__name__)


if sys.platform == "win32":
    import win32api
    import win32con
    import win32gui
    import win32process

    USER32 = ctypes.windll.user32

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("iu", _INPUTUNION)]


@dataclass(slots=True)
class TargetValidation:
    is_valid: bool
    reason: str


class PasteService:
    """Coordinates focus restore and Ctrl+V paste into the last external window."""

    def __init__(self, clipboard_service: ClipboardService) -> None:
        self._clipboard_service = clipboard_service
        self._supported = sys.platform == "win32"
        self._own_pid = os.getpid()
        self._last_foreground_window: int | None = None
        self._paste_delay_sec = 0.12

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
        LOGGER.info("Remembered foreground window: hwnd=%s", _format_hwnd(hwnd))

    def paste_item(self, item: ClipboardItem) -> bool:
        LOGGER.info("Action=paste_item item_id=%s item_type=%s", item.id, item.item_type.value)

        if item.item_type is not ClipboardItemType.TEXT:
            LOGGER.warning("Action=paste_item skipped_non_text item_id=%s item_type=%s", item.id, item.item_type.value)
            return False

        restored = self._clipboard_service.restore_item(item)
        if not restored:
            LOGGER.warning("Action=paste_item restore_failed item_id=%s", item.id)
            return False

        try:
            return self.paste_clipboard_to_previous_window()
        except Exception:
            LOGGER.exception("Action=paste_item unexpected_exception item_id=%s", item.id)
            return False

    def paste_clipboard_to_previous_window(self) -> bool:
        if not self._supported:
            LOGGER.warning("Action=paste platform_unsupported platform=%s", sys.platform)
            return False

        target_hwnd = self._last_foreground_window
        if target_hwnd is None:
            LOGGER.warning("Action=paste failed reason=no_remembered_window")
            return False

        validation = self._validate_target(target_hwnd)
        if not validation.is_valid:
            LOGGER.warning(
                "Action=paste failed reason=%s target_hwnd=%s", validation.reason, _format_hwnd(target_hwnd)
            )
            return False

        LOGGER.info("Action=paste focus_restore_start target_hwnd=%s", _format_hwnd(target_hwnd))
        if not self.restore_foreground_window(target_hwnd):
            LOGGER.warning("Action=paste failed reason=focus_restore_failed target_hwnd=%s", _format_hwnd(target_hwnd))
            return False

        time.sleep(self._paste_delay_sec)
        pasted = self.send_ctrl_v()
        if pasted:
            LOGGER.info("Action=paste success target_hwnd=%s", _format_hwnd(target_hwnd))
        else:
            LOGGER.warning("Action=paste failed reason=send_input_failed target_hwnd=%s", _format_hwnd(target_hwnd))
        return pasted

    def restore_foreground_window(self, target_hwnd: int) -> bool:
        if not self._supported:
            return False

        validation = self._validate_target(target_hwnd)
        if not validation.is_valid:
            LOGGER.warning(
                "Action=focus_restore skipped reason=%s target_hwnd=%s", validation.reason, _format_hwnd(target_hwnd)
            )
            return False

        if self._try_direct_focus_restore(target_hwnd):
            return True

        LOGGER.info("Action=focus_restore using_attach_thread_input target_hwnd=%s", _format_hwnd(target_hwnd))
        return self._try_attach_thread_input_fallback(target_hwnd)

    def send_ctrl_v(self) -> bool:
        if not self._supported:
            return False

        try:
            inputs = (
                self._keyboard_input(win32con.VK_CONTROL, key_up=False),
                self._keyboard_input(ord("V"), key_up=False),
                self._keyboard_input(ord("V"), key_up=True),
                self._keyboard_input(win32con.VK_CONTROL, key_up=True),
            )
            sent = USER32.SendInput(len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT))
            return sent == len(inputs)
        except Exception:
            LOGGER.exception("Action=send_ctrl_v exception")
            return False

    def _keyboard_input(self, vk_code: int, *, key_up: bool) -> INPUT:
        flags = KEYEVENTF_KEYUP if key_up else 0
        keyboard = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=flags, time=0, dwExtraInfo=None)
        return INPUT(type=INPUT_KEYBOARD, iu=_INPUTUNION(ki=keyboard))

    def _try_direct_focus_restore(self, target_hwnd: int) -> bool:
        try:
            if win32gui.IsIconic(target_hwnd):
                win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(target_hwnd)
            win32gui.SetForegroundWindow(target_hwnd)
        except Exception:
            LOGGER.exception("Action=focus_restore direct_failed target_hwnd=%s", _format_hwnd(target_hwnd))
            return False

        active_hwnd = win32gui.GetForegroundWindow()
        return active_hwnd == target_hwnd

    def _try_attach_thread_input_fallback(self, target_hwnd: int) -> bool:
        attached_threads: list[int] = []

        try:
            current_thread = win32api.GetCurrentThreadId()
            target_thread, _ = win32process.GetWindowThreadProcessId(target_hwnd)
            active_hwnd = win32gui.GetForegroundWindow()
            foreground_thread = 0
            if active_hwnd:
                foreground_thread, _ = win32process.GetWindowThreadProcessId(active_hwnd)

            for thread_id in {target_thread, foreground_thread}:
                if thread_id and thread_id != current_thread and USER32.AttachThreadInput(current_thread, thread_id, True):
                    attached_threads.append(thread_id)

            if win32gui.IsIconic(target_hwnd):
                win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(target_hwnd)
            win32gui.SetForegroundWindow(target_hwnd)
            win32gui.SetFocus(target_hwnd)
        except Exception:
            LOGGER.exception("Action=focus_restore attach_thread_failed target_hwnd=%s", _format_hwnd(target_hwnd))
            return False
        finally:
            current_thread = win32api.GetCurrentThreadId()
            for thread_id in attached_threads:
                try:
                    USER32.AttachThreadInput(current_thread, thread_id, False)
                except Exception:
                    LOGGER.debug("Action=focus_restore detach_failed thread=%s", thread_id)

        return win32gui.GetForegroundWindow() == target_hwnd

    def _is_external_window(self, hwnd: int) -> bool:
        if not self._supported or not win32gui.IsWindow(hwnd):
            return False

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid != 0 and pid != self._own_pid

    def _validate_target(self, hwnd: int) -> TargetValidation:
        if not self._supported:
            return TargetValidation(False, "platform_unsupported")
        if not hwnd:
            return TargetValidation(False, "missing_hwnd")
        if not win32gui.IsWindow(hwnd):
            return TargetValidation(False, "hwnd_not_found")
        if not self._is_external_window(hwnd):
            return TargetValidation(False, "internal_window")
        if not win32gui.IsWindowVisible(hwnd):
            return TargetValidation(False, "window_not_visible")
        if not win32gui.IsWindowEnabled(hwnd):
            return TargetValidation(False, "window_disabled")
        return TargetValidation(True, "ok")


def _format_hwnd(hwnd: int) -> str:
    return f"0x{int(hwnd):X}"
