from __future__ import annotations

import ctypes
import logging
import os
import sys
from ctypes import wintypes

from app.core.models import ClipboardItem
from app.services.clipboard_service import ClipboardService

LOGGER = logging.getLogger(__name__)


class PasteService:
    """Coordinates clipboard restore with foreground window focus and Ctrl+V simulation."""

    def __init__(self, clipboard_service: ClipboardService) -> None:
        self._clipboard_service = clipboard_service
        self._previous_window: int | None = None
        self._supported = sys.platform == "win32"
        self._own_pid = os.getpid()

    def remember_foreground_window(self) -> None:
        if not self._supported:
            self._previous_window = None
            return

        hwnd = _USER32.GetForegroundWindow()
        if not hwnd:
            return

        if not self._is_external_window(hwnd):
            LOGGER.debug("Skipped foreground window remember: hwnd=%s", _format_hwnd(hwnd))
            return

        self._previous_window = hwnd
        LOGGER.info("Remembered foreground window target: %s", _format_hwnd(hwnd))

    def paste_item(self, item: ClipboardItem) -> bool:
        LOGGER.info("Paste requested for item: %s (%s)", item.id, item.item_type.value)
        restored = self._clipboard_service.restore_item(item)
        if not restored:
            LOGGER.warning("Paste aborted: clipboard restore failed for item=%s", item.id)
            return False

        LOGGER.info("Clipboard restored for paste item: %s", item.id)
        return self.paste_clipboard_to_previous_window()

    def paste_clipboard_to_previous_window(self) -> bool:
        if not self._supported:
            LOGGER.warning("Paste simulation unavailable on platform: %s", sys.platform)
            return False

        if self._previous_window is None:
            LOGGER.warning("Paste failed: no previous foreground window remembered")
            return False

        target_hwnd = self._previous_window
        if not self._is_valid_target(target_hwnd):
            LOGGER.warning("Paste failed: invalid or unavailable target window: %s", _format_hwnd(target_hwnd))
            return False

        if not self._restore_focus(target_hwnd):
            LOGGER.warning("Paste failed: unable to restore target focus: %s", _format_hwnd(target_hwnd))
            return False

        LOGGER.info("Target window restored for paste: %s", _format_hwnd(target_hwnd))
        if not self._send_ctrl_v():
            LOGGER.warning("Paste failed: Ctrl+V simulation failed for target=%s", _format_hwnd(target_hwnd))
            return False

        LOGGER.info("Ctrl+V sent to target window: %s", _format_hwnd(target_hwnd))
        return True

    def _is_external_window(self, hwnd: int) -> bool:
        if not _USER32.IsWindow(hwnd):
            return False
        _, pid = _window_thread_process_id(hwnd)
        return pid != 0 and pid != self._own_pid

    def _is_valid_target(self, hwnd: int) -> bool:
        return bool(_USER32.IsWindow(hwnd)) and self._is_external_window(hwnd)

    def _restore_focus(self, target_hwnd: int) -> bool:
        if _USER32.GetForegroundWindow() == target_hwnd:
            return True

        current_thread = _KERNEL32.GetCurrentThreadId()
        target_thread, _ = _window_thread_process_id(target_hwnd)
        foreground_hwnd = _USER32.GetForegroundWindow()
        foreground_thread, _ = _window_thread_process_id(foreground_hwnd) if foreground_hwnd else (0, 0)

        attached_to_target = False
        attached_to_foreground = False
        try:
            if target_thread and target_thread != current_thread:
                attached_to_target = bool(_USER32.AttachThreadInput(current_thread, target_thread, True))
            if foreground_thread and foreground_thread != current_thread:
                attached_to_foreground = bool(_USER32.AttachThreadInput(current_thread, foreground_thread, True))

            if not _USER32.SetForegroundWindow(target_hwnd):
                return False
            _USER32.BringWindowToTop(target_hwnd)
            _USER32.SetFocus(target_hwnd)
            return _USER32.GetForegroundWindow() == target_hwnd
        finally:
            if attached_to_target:
                _USER32.AttachThreadInput(current_thread, target_thread, False)
            if attached_to_foreground:
                _USER32.AttachThreadInput(current_thread, foreground_thread, False)

    def _send_ctrl_v(self) -> bool:
        inputs = (_INPUT * 4)(
            _keyboard_input(_VK_CONTROL, 0),
            _keyboard_input(_VK_V, 0),
            _keyboard_input(_VK_V, _KEYEVENTF_KEYUP),
            _keyboard_input(_VK_CONTROL, _KEYEVENTF_KEYUP),
        )
        sent = _USER32.SendInput(len(inputs), ctypes.byref(inputs), ctypes.sizeof(_INPUT))
        return sent == len(inputs)


if sys.platform == "win32":
    _USER32 = ctypes.WinDLL("user32", use_last_error=True)
    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _VK_CONTROL = 0x11
    _VK_V = 0x56
    _INPUT_KEYBOARD = 1
    _KEYEVENTF_KEYUP = 0x0002

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", wintypes.ULONG_PTR),
        ]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT)]

    class _INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    _USER32.GetForegroundWindow.restype = wintypes.HWND
    _USER32.IsWindow.argtypes = [wintypes.HWND]
    _USER32.IsWindow.restype = wintypes.BOOL
    _USER32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _USER32.SetForegroundWindow.restype = wintypes.BOOL
    _USER32.BringWindowToTop.argtypes = [wintypes.HWND]
    _USER32.BringWindowToTop.restype = wintypes.BOOL
    _USER32.SetFocus.argtypes = [wintypes.HWND]
    _USER32.SetFocus.restype = wintypes.HWND
    _USER32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    _USER32.AttachThreadInput.restype = wintypes.BOOL
    _USER32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _USER32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
    _USER32.SendInput.restype = wintypes.UINT

    _KERNEL32.GetCurrentThreadId.restype = wintypes.DWORD

    def _window_thread_process_id(hwnd: int) -> tuple[int, int]:
        pid = wintypes.DWORD(0)
        thread_id = _USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(thread_id), int(pid.value)

    def _keyboard_input(virtual_key: int, flags: int) -> _INPUT:
        return _INPUT(type=_INPUT_KEYBOARD, ki=_KEYBDINPUT(wVk=virtual_key, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0))

else:
    _VK_CONTROL = 0
    _VK_V = 0
    _KEYEVENTF_KEYUP = 0

    class _INPUT(ctypes.Structure):
        _fields_ = []

    def _window_thread_process_id(hwnd: int) -> tuple[int, int]:
        return (0, 0)

    def _keyboard_input(virtual_key: int, flags: int) -> _INPUT:
        return _INPUT()


def _format_hwnd(hwnd: int) -> str:
    return f"0x{int(hwnd):X}"
