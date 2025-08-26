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

    def toggle_script(self):
        with self.lock:
            self.running = not self.running
            log.debug(f"Script is now {'running' if self.running else 'stopped'}")

    def exit_script(self):
        with self.lock:
            self.should_exit = True
        log.debug("Exiting script...")

    def start_listener(self):
        keyboard.add_hotkey("F10", self.toggle_script)
        log.debug("Hotkeys registered. F10=start/stop")
        # Keep the script running
        while not self.should_exit:
            keyboard.read_key()
