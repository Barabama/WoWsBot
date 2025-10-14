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


class TaskManager:
    """
    Simplified task manager that handles scheduled tasks with unified logic
    """

    def __init__(self):
        self.enabled = False
        self.tasks = []
        self.battle_counts = {}  # Track battles per task

    def load_tasks(self, data: dict):
        """Load tasks from user configuration"""
        self.enabled = data.get("enabled", False)
        self.tasks = []
        self.battle_counts = {}

        if not self.enabled:
            return

        for task_data in data.get("tasks", []):
            try:
                # Parse task data
                start_str = task_data["start"]
                end_str = task_data["end"]

                # Ensure time format includes minutes
                if ":" not in start_str:
                    start_str = f"{start_str}:00"
                if ":" not in end_str:
                    end_str = f"{end_str}:00"

                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                max_battles = int(task_data["count"])

                task = {
                    "start": start_time,
                    "end": end_time,
                    "max_battles": max_battles
                }

                self.tasks.append(task)
                # Initialize battle count for this task
                task_id = id(task)
                self.battle_counts[task_id] = 0

            except (ValueError, KeyError) as e:
                log.warning(f"Invalid scheduled task {task_data}, error: {e}")
                continue

    def is_running_time(self):
        """Check if current time is within any task's running time"""
        if not self.enabled or not self.tasks:
            return False

        current_time = datetime.now().time()

        for task in self.tasks:
            start_time = task["start"]
            end_time = task["end"]

            # Handle time ranges that cross midnight
            if start_time <= end_time:
                if start_time <= current_time <= end_time:
                    return True
            else:  # Crosses midnight
                if current_time >= start_time or current_time <= end_time:
                    return True

        return False

    def should_continue_running(self, in_battle=False):
        """
        Determine if script should continue running based on tasks and battle status
        If in battle, continue regardless of time constraints
        """
        if not self.enabled:
            return True

        if in_battle:
            return True

        # Check if we're in any task's running time
        return self.is_running_time()

    def record_battle(self):
        """Record that a battle has been completed"""
        if not self.enabled:
            return

        current_time = datetime.now().time()
        # Increment battle count for all active tasks
        for task in self.tasks:
            task_id = id(task)
            start_time = task["start"]
            end_time = task["end"]

            # Check if task is currently active
            if start_time <= end_time:
                is_active = start_time <= current_time <= end_time
            else:  # Crosses midnight
                is_active = current_time >= start_time or current_time <= end_time

            if is_active:
                self.battle_counts[task_id] = self.battle_counts.get(task_id, 0) + 1

    def is_finished_all_tasks(self):
        """Check if all tasks have reached their battle limit"""
        if not self.enabled or not self.tasks:
            return False

        for task in self.tasks:
            task_id = id(task)
            battles_done = self.battle_counts.get(task_id, 0)
            max_battles = task["max_battles"]

            # If any task hasn't reached its limit, we're not finished
            if battles_done < max_battles:
                return False

        # All tasks have reached their limits
        return True

    def reset_battle_counts(self):
        """Reset battle counts for all tasks"""
        for task_id in self.battle_counts:
            self.battle_counts[task_id] = 0


class MainController:
    def __init__(self, hkmgr: HotkeyManager):
        self.hkmgr = hkmgr
        self.running = False
        self.event_stop = threading.Event()
        self.task_manager = TaskManager()  # Use simplified task manager
        self.in_battle = False  # Track if we're currently in battle

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

            # Determine if we should continue running based on various conditions
            should_run = self.task_manager.should_continue_running(self.in_battle)
            log.debug(f"Should continue running: {should_run}, in_battle: {self.in_battle}")

            if should_run:
                self.tick()
            else:
                # If we shouldn't run but are currently running, stop the script
                if self.running:
                    log.info("No active tasks or outside scheduled time, stopping script")
                    self.event_stop.set()
        else:
            if self.running:
                self.on_stop()
            time.sleep(1)  # Slow down when not running

    def on_start(self):
        log.info("Script started")
        self.running = True
        self.event_stop.clear()

        self.arlctr = AreaLocator()
        self.task_manager.load_tasks(self.arlctr.user["scheduled_tasks"])

        self.wdmgr = WindowManager(region=tuple(self.arlctr.config["region"]),
                                   title=self.arlctr.user["title"])
        self.wdmgr.set_window_borderless()

        self.portbot = BotInPort(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)
        self.battlebot = BotInBattle(event=self.event_stop, arlctr=self.arlctr, wdmgr=self.wdmgr)

    def on_stop(self):
        log.info("Script stopped")
        self.running = False
        self.event_stop.set()

        self.in_battle = False
        self.task_manager.reset_battle_counts()
        del self.arlctr
        del self.wdmgr
        del self.portbot
        del self.battlebot

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
        self.in_battle = True

    def _handle_battle_start(self, match):
        """Handle the start of a battle"""
        log.info("Battle started - executing battle logic")
        self.in_battle = True
        self.battlebot.tick(match=match)

    def _handle_battle_end(self):
        """Handle the end of a battle"""
        log.info("Battle ended - executing post-battle logic")
        self.in_battle = False

        self.battlebot.quit_battle()
        self.task_manager.record_battle()

        # Check if we've finished all scheduled tasks
        if self.task_manager.is_finished_all_tasks():
            log.info("All scheduled tasks completed, stopping script")
            self.event_stop.set()

    def _handle_port_state(self, match):
        """Handle being in the port/harbor"""
        # Only log if we're transitioning from battle to port
        if self.in_battle:
            log.info("Returned to port - executing port logic")
        self.in_battle = False
        self.portbot.tick(match=match)
