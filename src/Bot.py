# src/Bot.py

import logging
import time
import random

import numpy as np
import pydirectinput as pdi

from .ArLctr import AreaLocator, Match
from .WinMgr import WindowManager

pdi.FAILSAFE = False

log = logging.getLogger(__name__)


def move(dx: int, dy: int):
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


def move_to(x: int, y: int):
    x_start, y_start = pdi.position()
    dx = x - x_start
    dy = y - y_start
    move(dx, dy)
    pdi.moveTo(x, y)


def click(button: str = "primary", clicks: int = 1, interval: float = 0.2):
    for i in range(clicks):
        pdi.mouseDown(button=button, duration=interval)
        pdi.mouseUp(button=button, duration=interval)
        time.sleep(random.uniform(interval, interval * 2))


def click_xy(x: int, y: int, clicks: int = 1, interval: float = 0.2):
    move_to(x, y)
    time.sleep(random.uniform(interval, interval * 2))
    click(clicks=clicks, interval=interval)
    time.sleep(random.uniform(interval, interval * 2))


def press_key(key: str, presses: int = 1, interval: float = 0.2):
    for i in range(presses):
        pdi.keyDown(key)
        time.sleep(random.uniform(interval, interval * 2))
        pdi.keyUp(key)
        time.sleep(random.uniform(interval, interval * 2))


class BotInPort:
    def __init__(self, arlctr: AreaLocator, wdmgr: WindowManager):
        self.arlctr = arlctr
        self.wdmgr = wdmgr

    def click_match(self, names: list[str]):
        screen = self.wdmgr.capture_screen()
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name in names:
            x, y, w, h = match.loc
            click_xy(x+w//2, y+h//2)
            return True
        return False

    def close_page(self):
        names = ["back_to_port_btn_1", "back_to_port_btn_2",
                 "close_btn_1", "close_btn_2", "esc_btn"]
        res = self.click_match(names)
        log.info(f"Close page: {res}")

    def select_battle(self, type: str = "coop"):
        # select battle type
        screen = self.wdmgr.capture_screen()
        mode = f"{type}_mode"
        btn = f"{type}_btn"
        names = [mode]
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name not in names:
            x, y, w, h = self.arlctr.config["templates"][mode]["area"]
            click_xy(x+w//2, y+h//2)
            self.click_match([btn])
        log.info("Selected battle type")

    def prepare_battle(self):
        # select ship
        pos_ship = self.arlctr.config["positions"]["ship_in_port"]
        click_xy(*pos_ship)
        log.info("Selected ship")

        # equipment
        pos_equip = self.arlctr.config["positions"]["equipment"]
        click_xy(*pos_equip)
        log.info("Selected equipment")

        # remove flag
        self.click_match(names=["flag_down"])
        log.info("Removed flag")

        # remove buff
        self.click_match(names=["buff_btn"])  # to show buff_btn
        pos_buff_btn = self.arlctr.config["positions"]["buff_btn"]
        click_xy(*pos_buff_btn)
        pos_buff_down_btn = self.arlctr.config["positions"]["buff_down_btn"]
        click_xy(*pos_buff_down_btn)
        self.click_match(names=["buff_down"])
        log.info("Removed buff")

        # back to port
        self.close_page()

    def start_battle(self):
        self.click_match(names=["battle_btn"])
        pos_confirm_btn = self.arlctr.config["positions"]["confirm_btn"]
        click_xy(*pos_confirm_btn)
        log.info("Started battle")

    def tick(self, match: Match):
        name = match.name

        if name in ["rewards_btn", "login_btn"]:
            x, y, w, h = match.loc
            click_xy(x+w//2, y+h//2)
            self.close_page()

        elif name == "battle_btn":
            self.select_battle()
            self.prepare_battle()
            self.start_battle()
        else:
            self.close_page()


class BotInBattle:
    def __init__(self, arlctr: AreaLocator, wdmgr: WindowManager):
        self.arlctr = arlctr
        self.wdmgr = wdmgr

    def set_autopilot(self):
        screen = self.wdmgr.capture_screen()
        names = ["autopilot_on"]
        match = self.arlctr.match_template(screen=screen, names=names)
        if match.name not in names:
            press_key("m")
            x, y, w, h = self.arlctr.config["region"]
            click_xy(x+w//2, y+h//2)
            press_key("m")
            press_key("+", presses=6, interval=0.5)
            press_key("-", presses=3, interval=0.5)

    def fire_weapon(self):
        for k in random.sample(["f", "g", "c", "r", "t", "y", "u", "i"], 2):
            press_key(k)
        
        # reset mouse
        press_key("ctrl")
        move(0, 1000)
        move(0, -465)

        # release torpedos or airbombs
        for k in random.sample(["3", "4"], 1):
            press_key(k)
            move(random.randint(-50, 50), 0)
            click()

        # main gun fire
        for k in random.sample(["1", "2"], 1):
            press_key(k, 2)
            move(random.randint(-20, 20), 0)
            time.sleep(2)
            click(clicks=2)

    def quit_battle(self):
        press_key("esc")
        time.sleep(1)
        press_key("space")

    def tick(self):
        self.set_autopilot()
        self.fire_weapon()
