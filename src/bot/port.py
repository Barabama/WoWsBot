# src/bot/port.py

import logging
import traceback
from threading import Event

import pydirectinput as pdi

from src.ArLctr import AreaLocator, Match
from src.WinMgr import WindowManager
from src.bot.base import BotBase

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


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
        """Try to close current page."""
        names = [
            "back_to_port_btn_1",
            "back_to_port_btn_2",
            "close_btn_1",
            "close_btn_2",
            "esc_btn",
        ]
        if not self._match_click(names):
            self._press_key("esc")
        log.info("Try to close page")

    def select_type(self, type: str = "coop") -> bool:
        """Select battle type."""
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
        """Select a ship."""
        try:
            log.info("Ship selecting...")
            pos_ship = self.arlctr.config["positions"]["ship_in_port"]
            self._move_to(*pos_ship)
            self._scroll(120, 2)  # scroll to top
            self._click(clicks=2)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def select_equipment(self) -> bool:
        """Select equipment."""
        try:
            log.info("Equipment selecting...")
            pos_equip = self.arlctr.config["positions"]["equipment"]
            self._click_xy(*pos_equip)
            return True
        except Exception:
            log.error(traceback.format_exc())
            return False

    def remove_flag(self) -> bool:
        """Remove flag."""
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
        """Remove buff."""
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
            return self._match_click(names=["buff_down_btn_1", "buff_down_btn_2"])
        except Exception as e:
            log.error(traceback.format_exc())
            return False

    def start_battle(self) -> bool:
        """Start battle."""
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
        """Main execution tick for port state."""
        name = match.name
        self.screen = match.screen

        names = ["rewards_btn", "login_btn", "accept_btn"]
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

        elif name in ["logining_1", "logining_2"]:
            log.info("Waiting for login...")

        else:
            self.close_page()
