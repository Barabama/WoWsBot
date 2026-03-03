# src/bot/battle.py

import random
import logging
import traceback
from datetime import datetime, timedelta
from threading import Event

import numpy as np
import pydirectinput as pdi

from src.ArLctr import AreaLocator, Match
from src.WinMgr import WindowManager
from src.bot.base import BotBase

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


class BotInBattle(BotBase):
    def __init__(self, event: Event, arlctr: AreaLocator, wdmgr: WindowManager):
        super().__init__(event, arlctr, wdmgr)

        self.show = log.level == logging.DEBUG
        self.timer_atpl = datetime.now()
        self.interval_atpl = 50
        self.sight = 0.0
        self.enemies: list[tuple[float, float]] = [(0.0, 0.0)]
        # self.sens_wide = 168 / (np.pi * 2)
        # self.sens_narrow = 1009 / (np.pi * 2)
        self.sens_wide = 5740 / (np.pi * 2)
        self.sens_narrow = 34437 / (np.pi * 2)

    def set_minimap(self) -> None:
        """Set size of minimap middle."""
        self._press_key("-", presses=6, interval=0.01)
        self._press_key("=", presses=3, interval=0.01)

    def open_bigmap(self) -> None:
        """Open bigmap."""
        if not self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")
            self._sleep(0.2)

    def close_bigmap(self) -> None:
        """Close bigmap."""
        if self._match(["map_mode", "b_btn"])[0]:
            self._press_key("m")
            self._sleep(0.2)

    def set_autopilot(self) -> bool:
        """Set autopilot."""
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
        """Build nautical chart for enemy detection."""
        try:
            # self._reset_mouse()
            self._sleep(0.2)
            self._capture_screen()
            if self.screen is None:
                return False

            delta = self.arlctr.read_compass(screen=self.screen, show=self.show)
            map_data = self.arlctr.read_minimap(screen=self.screen, show=self.show)
            if delta is None:
                log.warning("Delta in compass not found")
                return False
            if map_data is None:
                log.warning("Map data not found")
                return False

            # calculate sight
            sight = (0, -1)  # north
            mag_delta = np.sqrt(delta[0] ** 2 + delta[1] ** 2)
            mag_sight = np.sqrt(sight[0] ** 2 + sight[1] ** 2)
            dot_product = delta[0] * sight[0] + delta[1] * sight[1]
            cross_product = delta[0] * sight[1] - delta[1] * sight[0]
            angle_cos = dot_product / (mag_delta * mag_sight)
            angle_cos = np.clip(angle_cos, -1.0, 1.0)  # range in [-1, 1]
            angle_rad = np.arccos(angle_cos)
            angle_rad = -angle_rad if cross_product < 0 else angle_rad
            self.sight = (2 * np.pi - angle_rad) % (2 * np.pi)

            # handle map_data
            p_self, polar = map_data.get("self", [])
            polar_angle = np.arctan2(polar[0], polar[1])
            enemies = map_data.get("enemy", [])

            if len(enemies) > 0:
                enemies = np.array(enemies) - p_self
                dists = np.linalg.norm(enemies, axis=1)
                angles = np.arctan2(enemies[:, 1], enemies[:, 0])
                rads = angles - polar_angle
                rads = rads % (2 * np.pi)
                self.enemies = [(float(d), float(r)) for d, r in zip(dists, rads)]
                return True
            else:
                log.info("No enemy found")
                self.enemies = []
                return False

        except Exception:
            log.error(traceback.format_exc())
            return False

    # def open_scope(self):
    #     if self.arlctr.check_scope(screen=self)

    def search_enemy(self) -> None:
        """Search for the nearest enemy."""
        self.enemies.sort(key=lambda x: x[0])
        dist, rad = self.enemies[0]
        log.info(
            f"Cloest enemy found at distance {dist:.2f}, angle {np.rad2deg(rad):.2f}"
        )
        log.info(f"Self sight {np.rad2deg(self.sight):.2f}")
        diff = (rad - self.sight) % (2 * np.pi)
        pixel = round(diff * self.sens_wide)
        self._move_rel(pixel, 0)
        self._move_rel(0, 1000, 10)
        self._move_rel(0, -545, 10)
        self._sleep(1)

    def fire_weapon(self) -> None:
        """Fire weapons at enemy."""
        for k in random.sample(["f", "g", "c", "r", "t", "y", "u", "i"], 3):
            self._press_key(k)

        for k in random.sample(["1", "3", "4", "5"], 2):
            self._press_key(k, 2)
            self._sleep(2)
            self._click(clicks=2)
            self._click()

    def quit_battle(self) -> None:
        """Quit current battle."""
        self._press_key("esc")
        self._sleep(1)
        self._press_key("space")

    def tick(self, match: Match) -> None:
        """Main execution tick for battle state."""
        name = match.name
        self.screen = match.screen

        if name in ["map_mode", "b_btn"]:
            self.close_bigmap()

        elif not self._match(["autopilot_on"])[0] and self.timer_atpl < datetime.now():
            self.set_autopilot()

        elif self.build_nautical_chart():
            self.search_enemy()
            self.fire_weapon()
