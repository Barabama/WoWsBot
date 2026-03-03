# src/bot/base.py

import re
import time
import random
import logging
from threading import Event
from typing import Any

import win32api
import win32con
import numpy as np
import pydirectinput as pdi

from src.bot.input_ib import IbInputSimulator, SendType, MoveMode
from src.ArLctr import AreaLocator, Match
from src.WinMgr import WindowManager

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


class BotBase:
    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):

        libpath = "resources/bin/IbInputSimulator.dll"
        try:
            self.ib = IbInputSimulator(libpath, SendType.SendInput)
        except Exception as e:
            log.error(f"Error loading IbInputSimulator: {e}")
            self.ib = None
        self.event_stop = event
        self.arlctr = arlctr
        self.wdmgr = wdmgr
        self.screen: np.ndarray | None = None

    def _check_event(self) -> bool:
        """Check if event is set."""
        if self.event_stop.is_set():
            return True
        return False

    def _sleep(self, t: float):
        """Sleep randomly between t and 2t."""
        if self._check_event():
            return
        time.sleep(random.uniform(t, t * 2))

    def _move_rel(self, dx: int, dy: int, step: int = 200, ib: bool = True):
        """Move mouse relatively by (dx, dy)."""
        if self._check_event():
            return
        # Duration based on distance
        distance = abs(dx) + abs(dy)
        duration = max(0.1, min(0.2, distance / 10000))
        steps = int(duration * step)
        for i in range(1, steps + 1):
            if self._check_event():
                return
            ratio = i / steps
            if i == 1:
                step_dx = int(dx * ratio)
                step_dy = int(dy * ratio)
            else:
                prev_ratio = (i - 1) / steps
                step_dx = int(dx * ratio) - int(dx * prev_ratio)
                step_dy = int(dy * ratio) - int(dy * prev_ratio)

            jitter_x = random.uniform(-1, 1)
            jitter_y = random.uniform(-1, 1)
            step_dx += int(jitter_x)
            step_dy += int(jitter_y)

            if ib and self.ib:
                self.ib.move_mouse(step_dx, step_dy, MoveMode.Relative)
            else:
                pdi.moveRel(step_dx, step_dy)

            self._sleep(0.02)

    def _move_to(self, x: int, y: int, step: int = 50):
        """Move mouse to a point(x, y)."""
        if self._check_event():
            return
        x_start, y_start = pdi.position()
        dx = x - x_start
        dy = y - y_start

        self._move_rel(dx, dy, step, ib=False)
        pdi.moveTo(x, y)

    def _click(self, button: str = "primary", clicks: int = 1, interval: float = 0.1):
        """Click mouse button."""
        for i in range(clicks):
            if self._check_event():
                return
            pdi.mouseDown(button=button, duration=interval)
            pdi.mouseUp(button=button, duration=interval)
            self._sleep(interval)

    def _click_xy(
        self,
        x: int,
        y: int,
        button: str = "primary",
        clicks: int = 1,
        interval: float = 0.1,
    ):
        """Click at (x, y)."""
        self._move_to(x, y)
        self._sleep(interval)
        self._click(button, clicks, interval)
        self._sleep(interval)

    def _press_key(self, key: str, presses: int = 1, interval: float = 0.1):
        """Press keyboard key."""
        for i in range(presses):
            if self._check_event():
                return
            pdi.keyDown(key)
            self._sleep(interval)
            pdi.keyUp(key)
            self._sleep(interval)

    def _scroll(
        self, delta: int, scrolls: int = 1, interval: float = 0.1, ib: bool = True
    ):
        """Scroll mouse wheel."""
        for i in range(scrolls):
            if self._check_event():
                return
            if ib and self.ib:
                self.ib.mouse_wheel(delta)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
            self._sleep(interval)

    def _capture_screen(self, force: bool = False) -> np.ndarray:
        if self.screen is None or force:
            self._sleep(0.2)
            self.screen = self.wdmgr.capture_screen()
        return self.screen

    def _match(self, names: list[str]) -> tuple[bool, Match]:
        screen = self.screen if self.screen is not None else self._capture_screen()
        match = self.arlctr.match_template(screen=screen, names=names)
        return match.name in names, match

    def _match_click(self, names: list[str]) -> bool:
        flag, match = self._match(names)
        if flag:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)
        return flag
