# src/MCtrl.py

import logging
import sys
import time
import traceback

import numpy as np

from .ArLctr import AreaLocator
from .HkMgr import HotkeyManager
from .WinMgr import WindowManager
from .Bot import BotInPort, BotInBattle

log = logging.getLogger(__name__)


class MainController:
    def __init__(self, arlctr: AreaLocator, hkmgr: HotkeyManager, wdmgr: WindowManager,
                 portbot: BotInPort, battlebot: BotInBattle):
        self.arlctr = arlctr
        self.hkmgr = hkmgr
        self.wdmgr = wdmgr
        self.portbot = portbot
        self.battlebot = battlebot
        self.running = False

    def run(self):
        log.info("Main Controller Started")
        self.wdmgr.set_window_borderless()
        time.sleep(0.5)
        while not self.hkmgr.should_exit:
            if self.hkmgr.running:
                if not self.running:
                    self.on_start()
                self.tick()
            else:
                if self.running:
                    self.on_stop()
                time.sleep(2)  # slow down
        log.info("Main Controller exited")
        sys.exit(0)

    def on_start(self):
        log.info("Script started")
        self.running = True

    def on_stop(self):
        log.info("Script stopped")
        self.running = False

    def tick(self):
        screen = self.wdmgr.capture_screen()
        match = self.arlctr.match_template(screen=screen)
        name = match.name
        if name in ["battle_queue", "battle_member", "battle_mission"]:
            log.info(f"Waiting for battle")
            time.sleep(5)
        elif name in ["battle_began"]:
            log.info(f"Battle started")
            self.battlebot.tick()
            time.sleep(0.5)
        elif name in ["shift_btn", "f1_btn", "back_to_port_btn_2"]:
            log.info(f"Battle ended")
            self.battlebot.quit_battle()
        else:
            log.info(f"In port handle")
            self.portbot.tick(match=match)
            time.sleep(0.5)
