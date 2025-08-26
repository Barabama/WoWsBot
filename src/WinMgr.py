# /src/WinMgr.py

import logging
import time

import mss
import numpy as np
import win32gui
import win32con
import pygetwindow as gw

log = logging.getLogger(__name__)


class WindowManager:
    _region: list[int]
    window: gw.Win32Window

    def __init__(self, region: tuple[int], title: str):
        if len(region) != 4 or not all(isinstance(x, int) for x in region):
            raise ValueError("region must be 4-int list")
        self._region = region

        windows = gw.getWindowsWithTitle(title)
        if not windows:
            raise RuntimeError(f"Not found window with title: {title}")
        self.window = windows[0]
        log.info(f"Initialized window: {title}")

    def set_window_borderless(self):
        hwnd = win32gui.FindWindow(None, self.window.title)
        if not hwnd:
            raise RuntimeError("Not found window")
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        # Remove border
        style &= ~win32con.WS_CAPTION
        style &= ~win32con.WS_THICKFRAME
        style &= ~win32con.WS_MINIMIZEBOX
        style &= ~win32con.WS_MAXIMIZEBOX
        style &= ~win32con.WS_SYSMENU
        style |= win32con.WS_POPUP

        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        x, y, w, h = self._region
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, w, h, win32con.SWP_SHOWWINDOW)
        log.info(f"Set window to borderless")

    def check_window(self):
        if not self.window.isActive:
            self.window.activate()
        x, y, w, h = self._region
        if (self.window.left, self.window.top) != (x, y):
            self.window.moveTo(x, y)
            log.info("Reset window position")
        if (self.window.width, self.window.height) != (w, h):
            self.window.resizeTo(w, h)
            log.info("Reset window size")
        
    def capture_screen(self) -> np.ndarray:
        self.check_window()
        time.sleep(0.5)
        x, y, w, h = self._region
        monitor = {"top": y, "left": x, "width": w, "height": h}
        with mss.mss() as sct:
            img = np.array(sct.grab(monitor))
        return img[:, :, :3]  # BGR without alpha
