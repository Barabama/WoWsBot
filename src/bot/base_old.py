# src/bot/base.py

import time
import random
import logging
from threading import Event

import win32api
import win32con
import numpy as np
import pydirectinput as pdi

from src.ArLctr import AreaLocator, Match
from src.WinMgr import WindowManager

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


class BotBase:

    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
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

    def _move_to(self, x: int, y: int):
        """Move mouse to a point(x, y)."""
        if self._check_event():
            return
        x_start, y_start = pdi.position()
        dx = x - x_start
        dy = y - y_start

        # duration based on distance
        distance = abs(dx) + abs(dy)
        duration = max(0.1, min(0.2, distance / 10000))

        steps = int(duration * 100)  # step per 10ms
        for i in range(1, steps + 1):
            if self._check_event():
                return
            ratio = i / steps
            x_jitter = random.uniform(-2, 2)
            y_jitter = random.uniform(-2, 2)
            x_target = x_start + dx * ratio + x_jitter
            y_target = y_start + dy * ratio + y_jitter

            pdi.moveTo(int(x_target), int(y_target))
            # self._sleep(duration / steps * random.uniform(0.05, 0.1))

        if not self._check_event():
            pdi.moveTo(x, y)

    def _click(self, button: str = "primary", clicks: int = 1, interval: float = 0.1):
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
        self._move_to(x, y)
        self._sleep(interval)
        self._click(button=button, clicks=clicks, interval=interval)
        self._sleep(interval)

    def _press_key(self, key: str, presses: int = 1, interval: float = 0.1):
        for i in range(presses):
            if self._check_event():
                return
            pdi.keyDown(key)
            self._sleep(interval)
            pdi.keyUp(key)
            self._sleep(interval)

    def _scroll(
        self,
        direction: int | bool | str = False,
        srolls: int = 1,
        interval: float = 0.1,
    ):
        if self._check_event():
            return
        if direction in [0, False, "-", "down"]:
            symbol = "-"
        elif direction in [1, True, "+", "up"]:
            symbol = "+"
        else:
            raise ValueError("Invalid direction")
        dw = int(int(f"{symbol}120") * srolls)
        for i in range(srolls):
            if self._check_event():
                return
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, dw, 0)
            self._sleep(interval)

    def _reset_mouse(self):
        x_win, y_win, w_win, h_win = self.arlctr.config["region"]
        x_ct, y_ct = (x_win + w_win // 2, y_win + h_win // 2)
        pdi.keyDown("ctrl")
        pdi.moveTo(x_ct, y_ct)
        pdi.keyUp("ctrl")

    def _is_close_to_border(self, dx: int, dy: int, threshold: float) -> bool:
        x_win, y_win, w_win, h_win = self.arlctr.config["region"]
        x_max = x_win + w_win
        y_max = y_win + h_win
        x_curr, y_curr = pdi.position()
        x, y = x_curr + dx, y_curr + dy
        return (
            abs(x - x_win) <= threshold
            or abs(x - x_max) <= threshold
            or abs(y - y_win) <= threshold
            or abs(y - y_max) <= threshold
        )

    def _move_rel(self, dx: int, dy: int):
        """Move mouse relatively by dx, dy."""
        if self._check_event():
            return
        distance = abs(dx) + abs(dy)
        duration = max(0.1, min(0.2, distance / 10000))
        steps = int(duration * 100)
        dx_step, dy_step = dx / steps, dy / steps

        dx_sum = 0
        dy_sum = 0
        for i in range(steps):
            if self._check_event():
                return

            dx_next = int(dx_step)
            dy_next = int(dy_step)

            if self._is_close_to_border(
                dx_next, dy_next, threshold=max(abs(dx_next), abs(dy_next))
            ):
                self._reset_mouse()

            pdi.moveRel(dx_next, dy_next)
            dx_sum += dx_next
            dy_sum += dy_next
            self._sleep(duration / steps * random.uniform(0.01, 0.02))

        if not self._check_event():
            pdi.moveRel(dx - dx_sum, dy - dy_sum)

    def _capture_screen(self, force: bool = False):
        if self.screen is None or force:
            self._sleep(0.2)
            self.screen = self.wdmgr.capture_screen()

    def _match(self, names: list[str]) -> tuple[bool, Match]:
        if self.screen is None:
            self._capture_screen()
        match = self.arlctr.match_template(screen=self.screen, names=names)  # type: ignore
        return match.name in names, match

    def _match_click(self, names: list[str]) -> bool:
        flag, match = self._match(names)
        if flag:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)
        return flag
