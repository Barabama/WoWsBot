# src/MCtrl.py

import logging
import sys
import time
import traceback
import threading
from datetime import datetime

from .ArLctr import AreaLocator
from .HkMgr import HotkeyManager
from .WinMgr import WindowManager
from .Bot import BotInPort, BotInBattle

log = logging.getLogger(__name__)


def _is_time_in_range(time_start, time_end):
    """Check if a given time falls within a specified time range"""
    time_curr = datetime.now().time()
    if time_start <= time_end:
        return time_start <= time_curr <= time_end
    else:
        return time_curr >= time_start or time_curr <= time_end


class MainController:
    def __init__(self, hkmgr: HotkeyManager):
        self.hkmgr = hkmgr
        self.running = False
        self.event_stop = threading.Event()
        self.last_battle = False
        self.scheduled_tasks = {}
        self.active_tasks = {}
        self.in_battle = False  # Track if we're currently in battle
        self.tasks_counted_down = False  # Track if we've counted down tasks for current battle cycle

    def run(self):
        """Main controller loop"""
        log.info("Main Controller Started")
        try:
            while not self.hkmgr.should_exit:
                self._main_loop_iteration()
                time.sleep(1)  # Slow down loop
        except KeyboardInterrupt:
            log.info("Main Controller interrupted by user")
        except Exception as e:
            log.error(f"Unexpected error in Main Controller: {traceback.format_exc()}")
        finally:
            log.info("Main Controller exited")
            sys.exit(0)

    def _main_loop_iteration(self):
        """Handle one iteration of the main loop"""
        if self.hkmgr.running:
            if not self.running:
                self.on_start()

            # Process scheduled tasks
            self.check_tasks()

            # Determine if we should continue running based on various conditions
            should_run = self._should_continue_running()
            log.debug(f"Should continue running: {should_run}, in_battle: {self.in_battle}")

            if should_run:
                self.tick()
            else:
                # If we shouldn't run but are currently running, continue waiting for tasks
                if self.running:
                    log.info("No active tasks, waiting for scheduled tasks")
                    # Instead of stopping the script, we just wait
                    time.sleep(1)
        else:
            if self.running:
                self.on_stop()
            time.sleep(1)  # Slow down when not running

    def load_tasks(self, data: dict):
        if not data.get("enabled", False):
            return
        for task in data.get("tasks", []):
            try:
                start_str = task["start"]
                end_str = task["end"]
                if ":" not in start_str:
                    start_str = f"{start_str}:00"
                if ":" not in end_str:
                    end_str = f"{end_str}:00"
                start = datetime.strptime(start_str, "%H:%M").time()
                end = datetime.strptime(end_str, "%H:%M").time()
                typ = str(task["type"])
                count = int(task["count"])
                self.scheduled_tasks[(typ, start, end)] = count
            except (ValueError, KeyError) as e:
                log.warning(f"Invalid scheduled task {task}, error: {e}")
                continue

    def check_tasks(self):
        """Check and update scheduled tasks status"""
        # Remove expired or completed active tasks
        for id, count in list(self.active_tasks.items()):
            typ, start, end = id
            if not _is_time_in_range(start, end) or (count <= 0 and typ != "daily"):
                log.debug(f"Removing expired/complete task: {id}")
                self.active_tasks.pop(id)
            elif count <= 0 and typ == "daily":
                # For daily tasks, reset the count when time window is still active
                # This allows the task to repeat the next day
                original_count = self.scheduled_tasks.get(id, 0)
                if original_count > 0:
                    self.active_tasks[id] = original_count
                    log.debug(f"Reset daily task count: {id} to {original_count}")

        # Add scheduled tasks that are now in their time window
        for id, count in list(self.scheduled_tasks.items()):
            typ, start, end = id
            if not _is_time_in_range(start, end):
                continue

            log.debug(f"Activating scheduled task: {id}")
            self.active_tasks[id] = count

            # Single-use tasks are removed after activation
            if typ == "single":
                log.debug(f"Removing single-use task: {id}")
                self.scheduled_tasks.pop(id)

    def countdown_active_tasks(self):
        if len(self.scheduled_tasks) > 0 and len(self.active_tasks) > 0:
            # Count down all active tasks
            for id in self.active_tasks:
                self.active_tasks[id] -= 1
            
            # Check if all active non-daily tasks are completed (count <= 0)
            # Daily tasks don't count towards the completion condition
            uncompleted_non_daily_tasks = [
                count for (typ, _, _), count in 
                [(id, self.active_tasks[id]) for id in self.active_tasks] 
                if typ != "daily" and count > 0
            ]
            
            # If we have non-daily tasks and they are all completed, mark this as the last battle
            all_non_daily_tasks = [
                (typ, count) for (typ, _, _), count in 
                [(id, self.active_tasks[id]) for id in self.active_tasks] 
                if typ != "daily"
            ]
            
            if all_non_daily_tasks and not uncompleted_non_daily_tasks:
                self.last_battle = True
                log.info("All non-daily scheduled tasks completed. Marking this as the last battle.")

    def on_start(self):
        log.info("Script started")
        self.running = True
        self.event_stop.clear()

        self.arlctr = AreaLocator()
        self.load_tasks(self.arlctr.user["scheduled_tasks"])

        self.wdmgr = WindowManager(region=tuple(self.arlctr.config["region"]),
                                   title=self.arlctr.user["title"])
        self.wdmgr.set_window_borderless()

        self.portbot = BotInPort(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)
        self.battlebot = BotInBattle(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)

    def on_stop(self):
        log.info("Script stopped")
        self.running = False
        self.event_stop.set()

        self.last_battle = False
        self.scheduled_tasks = {}
        self.active_tasks = {}
        self.in_battle = False
        self.tasks_counted_down = False
        del self.arlctr
        del self.wdmgr
        del self.portbot
        del self.battlebot

    def _should_continue_running(self):
        """
        Determine if the script should continue running based on hotkey and scheduled tasks status.
        If we're in battle, continue until battle ends regardless of scheduled tasks.
        If we're in port, follow scheduled tasks strictly.
        """
        # If hotkey is off, we shouldn't run at all
        if not self.hkmgr.running:
            log.debug("Hotkey is off, should not continue running")
            return False

        # If we're in battle, continue regardless of scheduled tasks status
        if self.in_battle:
            log.debug("Currently in battle, should continue running regardless of scheduled tasks")
            return True

        # If scheduled tasks feature is enabled, check if there are active tasks
        if self.scheduled_tasks:
            # If there are active tasks, continue running
            if self.active_tasks:
                log.debug("Active tasks found, should continue running")
                return True
            else:
                log.debug("No active tasks, should not continue running")
                return False
        else:
            # If scheduled tasks feature is not enabled, always continue running
            log.debug("Scheduled tasks not enabled, should continue running")
            return True

    def tick(self):
        """Main execution tick - process current game state and take appropriate actions"""
        try:
            # Early exit if stop event is set
            if self.event_stop.is_set():
                log.debug("Stop event is set, skipping tick")
                return

            # Capture screen and match template to determine game state
            screen = self.wdmgr.capture_screen()
            match = self.arlctr.match_template(screen=screen)
            name = match.name

            # Check for stop event again after potentially time-consuming operations
            if self.event_stop.is_set():
                log.debug("Stop event is set after screen capture, skipping tick")
                return

            # Process game state and execute appropriate bot logic
            self._process_game_state(name, match)

            # Final check for stop event before completing tick
            if self.event_stop.is_set():
                log.debug("Stop event is set at end of tick")
                return

        except Exception as e:
            log.error(f"Error in tick: {traceback.format_exc()}")
            # Check one more time if we should exit after an error
            if self.event_stop.is_set():
                return

    def _process_game_state(self, state_name: str, match):
        """Process the current game state and execute appropriate actions"""
        if state_name in ["battle_loading", "battle_queue", "battle_mission",
                          "battle_member", "battle_tips"]:
            self._handle_battle_preparation()

        elif state_name in ["battle_began", "map_mode", "b_btn", "autopilot_on"]:
            self._handle_battle_start(match)

        elif state_name in ["shift_btn", "f1_btn", "back_to_port_btn_2"]:
            self._handle_battle_end()

        else:
            self._handle_port_state(match)

    def _handle_battle_preparation(self):
        """Handle states when battle is loading or in queue"""
        log.info("Waiting for battle to start")
        # If we're entering battle from port (not already in battle)
        if not self.in_battle:
            self.tasks_counted_down = False
        self.in_battle = True

    def _handle_battle_start(self, match):
        """Handle the start of a battle"""
        log.info("Battle started - executing battle logic")
        # If we're entering battle from port (not already in battle)
        if not self.in_battle:
            self.tasks_counted_down = False

        self.in_battle = True

        self.battlebot.tick(match=match)

        # Countdown tasks only once per battle cycle
        if not self.tasks_counted_down:
            self.countdown_active_tasks()
            self.tasks_counted_down = True

    def _handle_battle_end(self):
        """Handle the end of a battle"""
        log.info("Battle ended - executing post-battle logic")
        self.in_battle = False
        self.tasks_counted_down = False  # Reset for next battle cycle

        self.battlebot.quit_battle()

        if self.last_battle:
            log.info("Last battle completed, setting stop event")
            self.event_stop.set()

    def _handle_port_state(self, match):
        """Handle being in the port/harbor"""
        # Only log if we're transitioning from battle to port
        if self.in_battle:
            log.info("Returned to port - executing port logic")

        self.in_battle = False
        self.tasks_counted_down = False  # Reset for next battle cycle
        self.portbot.tick(match=match)
