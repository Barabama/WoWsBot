# src/Bot.py

import logging
import time
import random
import traceback
from datetime import datetime, timedelta
from typing import Any
from threading import Event

import numpy as np
import pydirectinput as pdi
import win32api
import win32con

from .ArLctr import AreaLocator, Match
from .WinMgr import WindowManager

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


class BotBase:

    def __init__(self):
        self.interrupt_event = None

    def set_interrupt_event(self, event: Event):
        self.interrupt_event = event

    def _check_interrupt(self) -> bool:
        """Check if interrupt event is set"""
        if self.interrupt_event and self.interrupt_event.is_set():
            return True
        return False

    def _sleep(self, t: float):
        """Sleep randomly between t and 2t"""
        if self._check_interrupt():
            return
        time.sleep(random.uniform(t, t * 2))

    def _move(self, dx: int, dy: int):
        """Move mouse by dx, dy"""
        if self._check_interrupt():
            return
        x_start, y_start = pdi.position()

        # duration based on distance
        distance = abs(dx) + abs(dy)
        duration = max(0.1, min(0.2, distance / 10000))

        steps = int(duration * 100)  # step per 10ms
        for i in range(1, steps + 1):
            if self._check_interrupt():
                return
            ratio = i / steps
            x_jitter = random.uniform(-2, 2)
            y_jitter = random.uniform(-2, 2)
            x_target = x_start + dx * ratio + x_jitter
            y_target = y_start + dy * ratio + y_jitter

            pdi.moveTo(int(x_target), int(y_target))
            time.sleep(duration / steps * random.uniform(0.5, 1.5))

    def _move_to(self, x: int, y: int):
        """Move mouse to a point(x, y)"""
        if self._check_interrupt():
            return
        x_start, y_start = pdi.position()
        dx = x - x_start
        dy = y - y_start
        self._move(dx, dy)
        if not self._check_interrupt():
            pdi.moveTo(x, y)

    def _click(self, button: str = "primary", clicks: int = 1, interval: float = 0.1):
        for i in range(clicks):
            if self._check_interrupt():
                return
            pdi.mouseDown(button=button, duration=interval)
            pdi.mouseUp(button=button, duration=interval)
            self._sleep(interval)

    def _click_xy(self, x: int, y: int, button: str = "primary", clicks: int = 1, interval: float = 0.1):
        self._move_to(x, y)
        self._sleep(interval)
        self._click(button=button, clicks=clicks, interval=interval)
        self._sleep(interval)

    def _press_key(self, key: str, presses: int = 1, interval: float = 0.1):
        for i in range(presses):
            if self._check_interrupt():
                return
            pdi.keyDown(key)
            self._sleep(interval)
            pdi.keyUp(key)
            self._sleep(interval)

    def _scroll(self, direction: Any = False, srolls: int = 1, interval: float = 0.1):
        if self._check_interrupt():
            return
        if direction in [0, False, "-", "down"]:
            symbol = "-"
        elif direction in [1, True, "+", "up"]:
            symbol = "+"
        else:
            raise ValueError("Invalid direction")
        dw = int(int(f"{symbol}120") * srolls)
        for i in range(srolls):
            if self._check_interrupt():
                return
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, dw, 0)
            self._sleep(interval)


class BotInPort(BotBase):
    def __init__(self, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__()
        self.arlctr = arlctr
        self.wdmgr = wdmgr

        # step flags
        self.selected = False
        self.prepared = False

    def _click_match(self, names: list[str]) -> bool:
        screen = self.wdmgr.capture_screen()
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name in names:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)
            return True
        return False

    def close_page(self):
        names = ["back_to_port_btn_1", "back_to_port_btn_2",
                 "close_btn_1", "close_btn_2", "esc_btn"]
        if not self._click_match(names):
            self._press_key("esc")
        log.info(f"Try to close page")

    def select_battle(self, type: str = "coop") -> bool:
        try:
            # select battle type
            screen = self.wdmgr.capture_screen()
            mode = f"{type}_mode"
            btn = f"{type}_btn"
            names = [mode]
            match = self.arlctr.match_template(screen=screen, names=names)
            if match.name not in names:
                x, y, w, h = self.arlctr.config["templates"][mode]["area"]
                self._click_xy(x + w // 2, y + h // 2)
                self._click_match([btn])
            log.info("Selected battle type")

            # select ship
            pos_ship = self.arlctr.config["positions"]["ship_in_port"]
            self._move_to(*pos_ship)
            self._scroll("down", 50)  # scroll to top
            self._click()
            log.info("Selected ship")
            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def prepare_battle(self) -> bool:
        try:
            # equipment
            pos_equip = self.arlctr.config["positions"]["equipment"]
            self._click_xy(*pos_equip)
            log.info("Selected equipment")

            # remove flag
            if self._click_match(names=["flag_down"]):
                log.info("Removed flag")

            # remove buff
            self._click_match(names=["buff_btn"])  # to show buff_btn
            pos_buff_btn = self.arlctr.config["positions"]["buff_btn"]
            pos_buff_down_btn = self.arlctr.config["positions"]["buff_down_btn"]
            self._click_xy(*pos_buff_down_btn)
            self._click_xy(*pos_buff_btn, button="secondary")
            self._click_match(names=["buff_down"])
            log.info("Removed buff")

            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def start_battle(self) -> bool:
        try:
            self._click_match(names=["battle_btn"])
            pos_confirm_btn = self.arlctr.config["positions"]["confirm_btn"]
            self._click_xy(*pos_confirm_btn)
            log.info("Started battle")
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def tick(self, match: Match):
        name = match.name

        if name in ["rewards_btn", "login_btn"]:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)

        elif name == "battle_btn" and not self.selected:
            self.selected = self.select_battle()

        elif name == "battle_btn" and not self.prepared:
            self.prepared = self.prepare_battle()

        elif name == "battle_btn":
            flag = self.start_battle()
            self.selected = not flag
            self.prepared = not flag

        else:
            self.close_page()


class BotInBattle(BotBase):
    def __init__(self, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__()
        self.arlctr = arlctr
        self.wdmgr = wdmgr
        self.timer_atpl = None
        self.interval_atpl = 100

    def set_minimap(self):
        """Set size of minimap middle"""
        self._press_key("-", presses=6, interval=0.01)
        self._press_key("=", presses=3, interval=0.01)

    def close_map(self):
        self._press_key("m")

    def set_autopilot(self) -> bool:
        try:
            self.set_minimap()
            screen = self.wdmgr.capture_screen()
            names = ["autopilot_on"]
            match = self.arlctr.match_template(screen=screen, names=names)
            if match.name in names:
                return True

            self._press_key("m")  # open bigmap
            if reds := self.arlctr.search_reds(screen=self.wdmgr.capture_screen()):
                # set a point random
                self._click_xy(*random.choice(reds))
            else:
                # set to middle
                x, y, w, h = self.arlctr.config["region"]
                self._click_xy(x + w // 2, y + h // 2)
            self._press_key("m")  # close bigmap

            # reset clock
            self.timer_atpl = datetime.now() + timedelta(seconds=self.interval_atpl)
            log.info("Autopilot set")
            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def fire_weapon(self):

        for k in random.sample(["f", "g", "c", "r", "t", "y", "u", "i"], 2):
            self._press_key(k)

        # reset mouse
        self._press_key("ctrl")
        self._move(0, 1000)
        self._move(0, -265)

        # release torpedos or airbombs
        for k in random.sample(["3", "4"], 1):
            self._press_key(k)
            self._move(random.randint(-50, 50), 0)
            self._click()

        # main gun fire
        for k in random.sample(["1", "2"], 1):
            self._press_key(k, 2)
            self._move(random.randint(-20, 20), 0)
            self._sleep(2)
            self._click(clicks=2)

    def quit_battle(self):
        self._press_key("esc")
        self._sleep(1)
        self._press_key("space")

    def tick(self, match: Match):
        name = match.name

        if name in ["map_mode", "b_btn"]:
            self.close_map()
        if self.timer_atpl is None or self.timer_atpl < datetime.now():
            self.set_autopilot()

        self.fire_weapon()
