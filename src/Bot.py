# src/Bot.py

import logging
import time
import random
import traceback
from datetime import datetime, timedelta
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

    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
        self.event_stop = event
        self.arlctr = arlctr
        self.wdmgr = wdmgr
        self.screen: np.ndarray | None = None

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

    def _move_to(self, x: int, y: int):
        """Move mouse to a point(x, y)"""
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

    def _scroll(self, direction: int | bool | str = False, srolls: int = 1, interval: float = 0.1):
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
        return (abs(x - x_win) <= threshold or
                abs(x - x_max) <= threshold or
                abs(y - y_win) <= threshold or
                abs(y - y_max) <= threshold)

    def _move_rel(self, dx: int, dy: int):
        """Move mouse relatively by dx, dy"""
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

            if self._is_close_to_border(dx_next, dy_next, threshold=max(abs(dx_next), abs(dy_next))):
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


class BotInPort(BotBase):
    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__(event, arlctr, wdmgr)

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

    def close_page(self) -> None:
        """Try to close current page"""
        names = ["back_to_port_btn_1", "back_to_port_btn_2",
                 "close_btn_1", "close_btn_2", "esc_btn"]
        if not self._match_click(names):
            self._press_key("esc")
        log.info("Try to close page")

    def select_type(self, type: str = "coop") -> bool:
        """Select battle type"""
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
        """Select a ship"""
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
        """Select equipment"""
        try:
            log.info("Equipment selecting...")
            pos_equip = self.arlctr.config["positions"]["equipment"]
            self._click_xy(*pos_equip)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def remove_flag(self) -> bool:
        """Remove flag"""
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
        """Remove buff"""
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
        """Start battle"""
        try:
            log.info("Battle starting...")
            self._match_click(names=["battle_btn"])
            pos_confirm_btn = self.arlctr.config["positions"]["confirm_btn"]
            self._click_xy(*pos_confirm_btn)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def tick(self, match: Match) -> None:
        """Main execution tick for port state"""
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
            elif not self.debuffed:
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
        super().__init__(event, arlctr, wdmgr)

        self.show = log.level == logging.DEBUG
        self.timer_atpl = datetime.now()
        self.interval_atpl = 100
        self.sight = 0.0
        self.enemies: list[tuple[float, float]] = [(0.0, 0.0)]
        self.sens_wide = 168 / (np.pi * 2)
        self.sens_narrow = 1009 / (np.pi * 2)

    def set_minimap(self) -> None:
        """Set size of minimap middle"""
        self._press_key("-", presses=6, interval=0.01)
        self._press_key("=", presses=3, interval=0.01)

    def open_bigmap(self) -> None:
        """Open bigmap"""
        if not self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")
            self._sleep(0.2)

    def close_bigmap(self) -> None:
        """Close bigmap"""
        if self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")
            self._sleep(0.2)

    def set_autopilot(self) -> bool:
        """Set autopilot"""
        try:
            log.info("Setting autopilot")
            self.open_bigmap()

            self._capture_screen(force=True)  # a new page bigmap
            if self.screen is not None:
                if reds := self.arlctr.read_bigmap(screen=self.screen, show=self.show):
                    # set a point random
                    self._click_xy(*random.choice(reds))
                else:
                    # # set to middle
                    # x, y, w, h = self.arlctr.config["region"]
                    # self._click_xy(x + w // 2, y + h // 2)
                    self._press_key("w", 5)
            else:
                self._press_key("w", 5)

            self.close_bigmap()
            log.info("Autopilot set")

            # reset clock
            self.timer_atpl = datetime.now() + timedelta(seconds=self.interval_atpl)
            return True

        except Exception:
            log.error(traceback.format_exc())
            return False

    def build_nautical_chart(self) -> bool:
        """Build nautical chart for enemy detection"""
        try:
            self._sleep(0.2)
            self._capture_screen()
            if self.screen is None:
                return False

            delta = self.arlctr.read_compass(screen=self.screen, show=self.show)
            map_data = self.arlctr.read_minimap(screen=self.screen, show=self.show)
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
                return True
            else:
                self.enemies = []
                return False

        except Exception:
            log.error(traceback.format_exc())
            return False

    # def open_scope(self):
    #     if self.arlctr.check_scope(screen=self)

    def search_enemy(self) -> None:
        """Search for the nearest enemy"""
        self.enemies.sort(key=lambda x: x[0])
        dist, rad = self.enemies[0]
        log.info(f"Enemy found at distance {dist:.2f}, angle {np.rad2deg(rad):.2f}")
        log.info(f"Self sight {np.rad2deg(self.sight):.2f}")
        diff = (rad - self.sight) % (2 * np.pi)
        pixel = round(diff * self.sens_wide)
        self._move_rel(pixel, 0)
        self._move_rel(0, 24)
        self._move_rel(0, -8)
        self._sleep(1)

    def fire_weapon(self) -> None:
        """Fire weapons at enemy"""
        for k in random.sample(["f", "g", "c", "r", "t", "y", "u", "i"], 2):
            self._press_key(k)

        # release torpedos or airbombs
        for k in random.sample(["3", "4"], 1):
            self._press_key(k)
            self._click()

        # main gun fire
        for k in random.sample(["1", "2"], 1):
            self._press_key(k, 2)
            self._sleep(2)
            self._click(clicks=2)

    def quit_battle(self) -> None:
        """Quit current battle"""
        self._press_key("esc")
        self._sleep(1)
        self._press_key("space")

    def tick(self, match: Match) -> None:
        """Main execution tick for battle state"""
        name = match.name
        self.screen = match.screen

        if name in ["map_mode", "b_btn"]:
            self.close_bigmap()

        elif not self._match(["autopilot_on"])[0] and self.timer_atpl < datetime.now():
            self.set_autopilot()

        elif self.build_nautical_chart():
            self.search_enemy()

        else:
            self.fire_weapon()
