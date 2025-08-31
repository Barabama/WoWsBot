# src/Bot.py

import logging
import time
import random
import traceback
from typing import Any

import numpy as np
import pydirectinput as pdi
import win32api
import win32con

from .ArLctr import AreaLocator, Match
from .WinMgr import WindowManager

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


class BotBase:

    def sleep(self, t: float):
        """Sleep randomly between t and 2t"""
        time.sleep(random.uniform(t, t * 2))

    def move(self, dx: int, dy: int):
        """Move mouse by dx, dy"""
        x_start, y_start = pdi.position()

        # duration based on distance
        distance = abs(dx) + abs(dy)
        duration = max(0.1, min(0.2, distance / 10000))

        steps = int(duration * 100)  # step per 10ms
        for i in range(1, steps + 1):
            ratio = i / steps
            x_jitter = random.uniform(-2, 2)
            y_jitter = random.uniform(-2, 2)
            x_target = x_start + dx * ratio + x_jitter
            y_target = y_start + dy * ratio + y_jitter

            pdi.moveTo(int(x_target), int(y_target))
            time.sleep(duration / steps * random.uniform(0.5, 1.5))

    def move_to(self, x: int, y: int):
        """Move mouse to a point(x, y)"""
        x_start, y_start = pdi.position()
        dx = x - x_start
        dy = y - y_start
        self.move(dx, dy)
        pdi.moveTo(x, y)

    def click(self, button: str = "primary", clicks: int = 1, interval: float = 0.2):
        for i in range(clicks):
            pdi.mouseDown(button=button, duration=interval)
            pdi.mouseUp(button=button, duration=interval)
            self.sleep(interval)

    def click_xy(self, x: int, y: int, button: str = "primary", clicks: int = 1, interval: float = 0.2):
        self.move_to(x, y)
        self.sleep(interval)
        self.click(button=button, clicks=clicks, interval=interval)
        self.sleep(interval)

    def press_key(self, key: str, presses: int = 1, interval: float = 0.2):
        for i in range(presses):
            pdi.keyDown(key)
            self.sleep(interval)
            pdi.keyUp(key)
            self.sleep(interval)

    def scroll(self, direction: Any = False, srolls: int = 1, interval: float = 0.01):
        if direction in [0, False, "-", "down"]:
            symbol = "-"
        elif direction in [1, True, "+", "up"]:
            symbol = "+"
        else:
            raise ValueError("Invalid direction")
        dw = int(int(f"{symbol}120") * srolls)
        for i in range(srolls):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, dw, 0)
            self.sleep(interval)


class BotInPort(BotBase):
    def __init__(self, arlctr: AreaLocator, wdmgr: WindowManager):
        self.arlctr = arlctr
        self.wdmgr = wdmgr

        # step flags
        self.selected = False
        self.prepared = False

    def click_match(self, names: list[str]) -> bool:
        screen = self.wdmgr.capture_screen()
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name in names:
            x, y, w, h = match.loc
            self.click_xy(x+w//2, y+h//2)
            return True
        return False

    def close_page(self):
        names = ["back_to_port_btn_1", "back_to_port_btn_2",
                 "close_btn_1", "close_btn_2", "esc_btn"]
        res = self.click_match(names)
        log.info(f"Close page: {res}")

    def select_battle(self, type: str = "coop") -> bool:
        try:
            # select ship
            pos_ship = self.arlctr.config["positions"]["ship_in_port"]
            self.move_to(*pos_ship)
            self.scroll("down", 50)  # scroll to top
            self.click()
            log.info("Selected ship")

            # select battle type
            screen = self.wdmgr.capture_screen()
            mode = f"{type}_mode"
            btn = f"{type}_btn"
            names = [mode]
            match = self.arlctr.match_template(screen=screen, names=names)
            if match.name not in names:
                x, y, w, h = self.arlctr.config["templates"][mode]["area"]
                self.click_xy(x+w//2, y+h//2)
                self.click_match([btn])
            log.info("Selected battle type")

            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def prepare_battle(self) -> bool:
        try:
            # equipment
            pos_equip = self.arlctr.config["positions"]["equipment"]
            self.click_xy(*pos_equip)
            log.info("Selected equipment")

            # remove flag
            if self.click_match(names=["flag_down"]):
                log.info("Removed flag")

            # remove buff
            self.click_match(names=["buff_btn"])  # to show buff_btn
            pos_buff_btn = self.arlctr.config["positions"]["buff_btn"]
            self.click_xy(*pos_buff_btn, button="secondary")
            pos_buff_down_btn = self.arlctr.config["positions"]["buff_down_btn"]
            self.click_xy(*pos_buff_down_btn)
            self.click_match(names=["buff_down"])
            log.info("Removed buff")

            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def start_battle(self) -> bool:
        try:
            self.click_match(names=["battle_btn"])
            pos_confirm_btn = self.arlctr.config["positions"]["confirm_btn"]
            self.click_xy(*pos_confirm_btn)
            log.info("Started battle")
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def tick(self, match: Match):
        name = match.name

        if name in ["rewards_btn", "login_btn"]:
            x, y, w, h = match.loc
            self.click_xy(x+w//2, y+h//2)

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
        self.arlctr = arlctr
        self.wdmgr = wdmgr

    def set_autopilot(self):
        screen = self.wdmgr.capture_screen()
        names = ["autopilot_on"]
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name not in names:
            self.press_key("m")
            x, y, w, h = self.arlctr.config["region"]
            self.click_xy(x+w//2, y+h//2)
            self.press_key("m")
            self.press_key("+", presses=3, interval=0.5)
            self.press_key("-", presses=6, interval=0.5)

    def fire_weapon(self):
        for k in random.sample(["f", "g", "c", "r", "t", "y", "u", "i"], 2):
            self.press_key(k)

        # reset mouse
        self.press_key("ctrl")
        self.move(0, 1000)
        self.move(0, -465)

        # release torpedos or airbombs
        for k in random.sample(["3", "4"], 1):
            self.press_key(k)
            self.move(random.randint(-50, 50), 0)
            self.click()

        # main gun fire
        for k in random.sample(["1", "2"], 1):
            self.press_key(k, 2)
            self.move(random.randint(-20, 20), 0)
            self.sleep(2)
            self.click(clicks=2)

    def quit_battle(self):
        self.press_key("esc")
        self.sleep(1)
        self.press_key("space")

    def tick(self):
        self.set_autopilot()
        self.fire_weapon()
