# src/WinMgr.py

import logging
import time

import numpy as np
import win32gui
import win32con
import pygetwindow as gw
import mss

log = logging.getLogger(__name__)


class WindowManager:
    region: tuple[int, int, int, int]
    window: gw.Win32Window

    def __init__(self, region: tuple[int, int, int, int], window: gw.Win32Window):
        if len(region) != 4 or not all(isinstance(x, int) for x in region):
            raise ValueError("region must be 4-int list")
        self.region = region
        self.window = window
        log.info(f"Initialized window: {self.window.title}")

    def set_window_borderless(self):
        self.window.activate()
        time.sleep(1)  # wait for activation
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
        x, y, w, h = self.region
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, w, h, win32con.SWP_SHOWWINDOW)
        log.info(f"Set window {self.window.title} to borderless")
        time.sleep(1)

    def check_window(self):
        if not self.window.isActive:
            self.window.activate()
        x, y, w, h = self.region
        if (self.window.left, self.window.top) != (x, y):
            self.window.moveTo(x, y)
            log.info(f"Reset window {self.window.title} position")
        if (self.window.width, self.window.height) != (w, h):
            self.window.resizeTo(w, h)
            log.info(f"Reset window {self.window.title} size")

    def capture_screen(self, delay=1) -> np.ndarray:
        self.check_window()
        time.sleep(delay)
        x, y, w, h = self.region
        monitor = {"top": y, "left": x, "width": w, "height": h}
        with mss.mss() as sct:
            img = np.array(sct.grab(monitor))
        return img[:, :, :3]  # BGR without alpha