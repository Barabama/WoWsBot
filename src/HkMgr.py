# src/HKMgr.py

import logging
import threading

import keyboard


log = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self):
        self.running = False
        self.should_exit = False
        self.lock = threading.Lock()

    def script_start(self):
        with self.lock:
            self.running = True
            log.debug(f"Script is now running")

    def script_stop(self):
        with self.lock:
            self.running = False
            log.debug(f"Script is now stopped")

    def script_exit(self):
        with self.lock:
            self.should_exit = True
        log.debug("Exiting script...")

    def start_listener(self):
        keyboard.add_hotkey("F10", self.script_start)
        keyboard.add_hotkey("F11", self.script_stop)
        log.debug("Hotkeys registered. F10=start, F11=stop")
        # Keep the script running in a blocking way
        keyboard.wait()
