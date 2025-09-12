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

    def __init__(self, event: Event):
        self.event_stop = event

    def _check_event(self) -> bool:
        """Check if event is set"""
        if self.event_stop.is_set():
            return True
        return False

    def _sleep(self, t: float):
        """Sleep randomly between t and 2t"""
        if self._check_event():
            return
        time.sleep(random.uniform(t, t * 2))

    def _move(self, dx: int, dy: int):
        """Move mouse by dx, dy"""
        if self._check_event():
            return
        x_start, y_start = pdi.position()

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
            time.sleep(duration / steps * random.uniform(0.5, 1.5))

    def _move_to(self, x: int, y: int):
        """Move mouse to a point(x, y)"""
        if self._check_event():
            return
        x_start, y_start = pdi.position()
        dx = x - x_start
        dy = y - y_start
        self._move(dx, dy)
        if not self._check_event():
            pdi.moveTo(x, y)

    def _click(self, button: str = "primary", clicks: int = 1, interval: float = 0.1):
        for i in range(clicks):
            if self._check_event():
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
            if self._check_event():
                return
            pdi.keyDown(key)
            self._sleep(interval)
            pdi.keyUp(key)
            self._sleep(interval)

    def _scroll(self, direction: Any = False, srolls: int = 1, interval: float = 0.1):
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


class BotInPort(BotBase):
    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__(event=event)
        self.arlctr = arlctr
        self.wdmgr = wdmgr

        # step flags
        self.typed = False
        self.selected = False
        self.equipped = False
        self.deflaged = False
        self.debuffed = False

    def _capture_screen(self, force: bool = False):
        if self.screen is None or force:
            self._sleep(0.5)
            self.screen = self.wdmgr.capture_screen()

    def _match(self, names: list[str]) -> tuple[bool, Match]:
        match = self.arlctr.match_template(screen=self.screen, names=names)
        return match.name in names, match

    def _match_click(self, names: list[str]) -> bool:
        flag, match = self._match(names)
        if flag:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)
        return flag

    def close_page(self):
        names = ["back_to_port_btn_1", "back_to_port_btn_2",
                 "close_btn_1", "close_btn_2", "esc_btn"]
        if not self._match_click(names):
            self._press_key("esc")
        log.info(f"Try to close page")

    def select_type(self, type: str = "coop") -> bool:
        mode = f"{type}_mode"
        btn = f"{type}_btn"
        try:
            log.info(f"Battle type {type} selecting...")
            flag, match = self._match(names=[mode])
            if flag:
                return flag
            x, y, w, h = self.arlctr.config["templates"][mode]["area"]
            self._click_xy(x + w // 2, y + h // 2)
            self._capture_screen(force=True)  # a new type seelected page
            return self._match_click(names=[btn])

        except Exception:
            log.error(traceback.format_exc())
            return False

    def select_ship(self) -> bool:
        try:
            log.info("Ship selecting...")
            pos_ship = self.arlctr.config["positions"]["ship_in_port"]
            self._move_to(*pos_ship)
            self._scroll("up", 20)  # scroll to top
            self._click()
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def select_equipment(self) -> bool:
        try:
            log.info("Equipment selecting...")
            pos_equip = self.arlctr.config["positions"]["equipment"]
            self._click_xy(*pos_equip)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def remove_flag(self) -> bool:
        try:
            log.info("Flag removing...")
            flag, match = self._match(names=["flag_up_btn"])
            if flag:
                return True
            return self._match_click(["flag_down_btn"])
        except Exception as e:
            log.error(traceback.format_exc())
            return False

    def remove_buff(self) -> bool:
        try:
            log.info("Buff removing...")
            self._match_click(names=["buff_fold_btn"])  # to show buff_btn
            pos_buff_down_mod_btn = self.arlctr.config["positions"]["buff_down_mod_btn"]
            self._click_xy(*pos_buff_down_mod_btn)  # use mod to remove buff
            pos_buff_page_btn = self.arlctr.config["positions"]["buff_page_btn"]
            self._click_xy(*pos_buff_page_btn, button="secondary")  # to show buff page

            self._capture_screen(force=True)  # a new page
            flag, match = self._match(names=["buff_up_btn"])
            if flag:
                return flag
            return self._match_click(names=["buff_down_btn"])
        except Exception as e:
            log.error(traceback.format_exc())
            return False

    def start_battle(self) -> bool:
        try:
            log.info("Battle starting...")
            self._match_click(names=["battle_btn"])
            pos_confirm_btn = self.arlctr.config["positions"]["confirm_btn"]
            self._click_xy(*pos_confirm_btn)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def tick(self, match: Match):
        name = match.name
        self.screen = match.screen

        names = ["rewards_btn", "login_btn"]
        if name in names:
            self._match_click(names)

        elif name == "battle_btn":
            if not self.typed:
                self.typed = self.select_type()
            elif not self.selected:
                self.selected = self.select_ship()
            elif not self.equipped:
                self.equipped = self.select_equipment()
            elif not self.deflaged:
                self.deflaged = self.remove_flag()
            elif not self.deflaged:
                self.debuffed = self.remove_buff()
            else:
                flag = self.start_battle()
                self.typed = not flag
                self.selected = not flag
                self.equipped = not flag
                self.deflaged = not flag
                self.debuffed = not flag

        else:
            self.close_page()


class BotInBattle(BotBase):
    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__(event=event)
        self.arlctr = arlctr
        self.wdmgr = wdmgr
        self.timer_atpl = datetime.now()
        self.interval_atpl = 100
        self.sight = 0.0
        self.enemies = [(0.0, 0.0)]

    def _capture_screen(self, force: bool = False):
        if self.screen is None or force:
            self._sleep(0.5)
            self.screen = self.wdmgr.capture_screen()

    def _match(self, names: list[str]) -> tuple[bool, Match]:
        match = self.arlctr.match_template(screen=self.screen, names=names)
        return match.name in names, match

    def _match_click(self, names: list[str]) -> bool:
        flag, match = self._match(names)
        if flag:
            x, y, w, h = match.loc
            self._click_xy(x + w // 2, y + h // 2)
        return flag

    def set_minimap(self):
        """Set size of minimap middle"""
        self._press_key("-", presses=6, interval=0.01)
        self._press_key("=", presses=3, interval=0.01)

    def open_bigmap(self):
        if not self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")

    def close_bigmap(self):
        if self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")

    def set_autopilot(self) -> bool:
        try:
            flag, match = self._match(["autopilot_on"])
            if flag and self.timer_atpl > datetime.now():
                return True

            log.info("Setting autopilot")
            self.open_bigmap()

            self._capture_screen(force=True)  # a new page bigmap
            if reds := self.arlctr.read_bigmap(screen=self.screen):
                # set a point random
                self._click_xy(*random.choice(reds))
            else:
                # set to middle
                x, y, w, h = self.arlctr.config["region"]
                self._click_xy(x + w // 2, y + h // 2)

            self.close_bigmap()
            log.info("Autopilot set")

            # reset clock
            self.timer_atpl = datetime.now() + timedelta(seconds=self.interval_atpl)
            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def build_nautical_chart(self):
        delta = self.arlctr.read_compass(self.screen)
        map_data = self.arlctr.read_minimap(self.screen)
        if delta is None:
            return False
        if map_data is None:
            return False

        # calculate sight
        sight = (0, -1)  # north
        mag_delta = np.sqrt(delta[0]**2 + delta[1]**2)
        mag_sight = np.sqrt(sight[0]**2 + sight[1]**2)
        dot_product = delta[0] * sight[0] + delta[1] * sight[1]
        cross_product = delta[0] * sight[1] - delta[1] * sight[0]
        angle_cos = dot_product / (mag_delta * mag_sight)
        angle_cos = np.clip(angle_cos, -1.0, 1.0)  # range in [-1, 1]
        angle_rad = np.arccos(angle_cos)
        angle_rad = -angle_rad if cross_product < 0 else angle_rad
        self.sight = (2 * np.pi - angle_rad) % (2 * np.pi)

        # handle map_data
        p_self, polar = map_data["self"]
        polar_angle = np.arctan2(polar[0], polar[1])
        enemies = map_data["enemy"]
        
        if len(enemies) > 0:
            enemies = np.array(enemies) - p_self
            dists = np.linalg.norm(enemies, axis=1)
            angles = np.arctan2(enemies[:, 1], enemies[:, 0])
            rads = angles - polar_angle
            rads = rads % (2 * np.pi)
            self.enemies = [(float(d), float(r)) for d, r in zip(dists, rads)]
        else:
            self.enemies = []

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
        self.screen = match.screen

        if name in ["map_mode", "b_btn"]:
            self.close_bigmap()

        # self.set_autopilot()

        self.build_nautical_chart()

        # self.fire_weapon()
