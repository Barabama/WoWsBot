# src/MCtrl.py

import logging
import sys
import time
import traceback
import threading

import numpy as np

from .ArLctr import AreaLocator
from .HkMgr import HotkeyManager
from .WinMgr import WindowManager
from .Bot import BotInPort, BotInBattle

log = logging.getLogger(__name__)


class MainController:
    def __init__(self, arlctr: AreaLocator, hkmgr: HotkeyManager, wdmgr: WindowManager,):
        self.arlctr = arlctr
        self.hkmgr = hkmgr
        self.wdmgr = wdmgr
        self.running = False
        self.event_stop = threading.Event()

    def run(self):
        log.info("Main Controller Started")
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
        self.event_stop.clear()
        self.wdmgr.set_window_borderless()
        self.portbot = BotInPort(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)
        self.battlebot = BotInBattle(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)

    def on_stop(self):
        log.info("Script stopped")
        self.running = False
        self.event_stop.set()

    def tick(self):
        try:
            if self.event_stop.is_set():
                return

            screen = self.wdmgr.capture_screen()
            match = self.arlctr.match_template(screen=screen)
            name = match.name

            if self.event_stop.is_set():
                return

            if name in ["battle_loading", "battle_queue", "battle_mission",
                        "battle_member", "battle_tips"]:
                log.info(f"Waiting for battle")

            elif name in ["battle_began", "map_mode", "b_btn", "autopilot_on"]:
                log.info(f"Battle started")
                self.battlebot.tick(match=match)

            elif name in ["shift_btn", "f1_btn", "back_to_port_btn_2"]:
                log.info(f"Battle ended")
                self.battlebot.quit_battle()

            else:
                log.info(f"In port handle")
                self.portbot.tick(match=match)

            if self.event_stop.is_set():
                return

            time.sleep(1)
        except Exception as e:
            log.error(f"Error in tick: {traceback.format_exc()}")
            if self.event_stop.is_set():
                return
