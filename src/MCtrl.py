# src/MCtrl.py

import logging
import os
import sys
import time
import traceback
import threading
from datetime import datetime

import pygetwindow as gw

from .ArLctr import AreaLocator, Match, load_config, load_user
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
        self._task_ids = []  # Track task IDs for consistent counting

    def load_tasks(self, data: dict):
        """Load tasks from user configuration"""
        self.enabled = data.get("enabled", False)
        self.tasks = []
        self._task_ids = []
        self.battle_counts = {}

        if not self.enabled:
            return

        for i, task_data in enumerate(data.get("tasks", [])):
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
                # Use consistent task ID based on task position
                task_id = i
                self._task_ids.append(task_id)
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
        for i, task in enumerate(self.tasks):
            task_id = self._task_ids[i] if i < len(self._task_ids) else i
            start_time = task["start"]
            end_time = task["end"]

            # Check if task is currently active
            if start_time <= end_time:
                is_active = start_time <= current_time <= end_time
            else:  # Crosses midnight
                is_active = current_time >= start_time or current_time <= end_time

            if is_active:
                self.battle_counts[task_id] = self.battle_counts.get(task_id, 0) + 1
                log.debug(f"Task {task_id} recorded battle. Count now: {self.battle_counts[task_id]}")

    def is_finished_all_tasks(self):
        """Check if all tasks have reached their battle limit"""
        if not self.enabled or not self.tasks:
            return False

        for i, task in enumerate(self.tasks):
            task_id = self._task_ids[i] if i < len(self._task_ids) else i
            battles_done = self.battle_counts.get(task_id, 0)
            max_battles = task["max_battles"]

            # If any task hasn't reached its limit, we're not finished
            if battles_done < max_battles:
                log.debug(f"Task {task_id} not finished. Battles: {battles_done}/{max_battles}")
                return False

        # All tasks have reached their limits
        log.info("All tasks finished")
        return True

    def reset_battle_counts(self):
        """Reset battle counts for all tasks"""
        for task_id in self.battle_counts:
            self.battle_counts[task_id] = 0
        log.info("Battle counts reset")


class GameInstance:
    """Wrapper class for a game instance"""

    def __init__(self, idx: int, window: gw.Win32Window, region: tuple[int, int, int, int]):
        self.idx = idx
        self.window = window
        self.region = region
        self.wdmgr: WindowManager | None = None
        self.alctr: AreaLocator | None = None
        self.portbot: BotInPort | None = None
        self.battlebot: BotInBattle | None = None
        self.event_stop = threading.Event()
        self.task_manager = TaskManager()  # Use simplified task manager
        self.in_battle = False  # Track if we're currently in battle
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize game instance"""
        try:
            self.wdmgr = WindowManager(region=self.region, window=self.window)
            self.wdmgr.set_window_borderless()
            self.alctr = AreaLocator(win_title=self.window.title)
            if self.alctr and self.alctr.user:
                self.task_manager.load_tasks(data=self.alctr.user["scheduled_tasks"])
            self.portbot = BotInPort(event=self.event_stop, arlctr=self.alctr, wdmgr=self.wdmgr)
            self.battlebot = BotInBattle(event=self.event_stop, arlctr=self.alctr, wdmgr=self.wdmgr)
            self.initialized = True
            log.info(f"Game instance {self.idx} for {self.window.title} initialized")
            return True
        except Exception as e:
            log.error(f"Failed to initialize game instance {self.idx} for {self.window.title}")
            log.error(traceback.format_exc())
            return False

    def cleanup(self):
        """Cleanup game instance"""
        try:
            self.event_stop.set()
            self.wdmgr = None
            self.alctr = None
            self.portbot = None
            self.battlebot = None
            self.initialized = False
            log.info(f"Game instance {self.idx} for {self.window.title} cleaned up")
        except Exception:
            log.error(f"Game instance {self.idx} for {self.window.title} cleanup failed")
            log.error(traceback.format_exc())


class MainController:
    def __init__(self, hkmgr: HotkeyManager):
        self.hkmgr = hkmgr
        self.running = False
        self.stop_event = threading.Event()

        self.event_stop = threading.Event()
        self.task_manager = TaskManager()  # Use simplified task manager
        self.in_battle = False  # Track if we're currently in battle

    def setup_instances(self):
        """Set up game instances"""
        config = load_config(os.path.join("resources", "config.json"))
        user = load_user(os.path.join("resources", "user.json"))
        titles = list(user["title_lang_map"].keys())
        windows: list[gw.Win32Window] = []
        for t in titles:
            ws: list[gw.Win32Window] = gw.getWindowsWithTitle(t)
            windows.extend(ws)
        if len(windows) <= 0:
            raise RuntimeError("No game windows found")

        self.instances: list[GameInstance] = []
        for i, w in enumerate(windows):
            instance = GameInstance(idx=i, window=w, region=tuple(config["region"]))
            if instance.initialize():  # 初始化实例
                self.instances.append(instance)
            else:
                log.error(f"Failed to initialize instance for window: {w.title}")

        log.info(f"Set up {len(self.instances)} game instances")

    def on_start(self):
        """Start game instances"""
        log.info("Starting multi-controller")
        try:
            self.setup_instances()
            if self.instances and any(inst.initialized for inst in self.instances):
                self.running = True
                log.info("Multi-controller started")
            else:
                self.running = False
                log.error("No game instances initialized")
        except Exception as e:
            log.error(f"Failed to start multi-controller: {e}")
            log.error(traceback.format_exc())

    def on_stop(self):
        """Stop game instances"""
        log.info("Stopping multi-controller")
        for inst in self.instances:
            inst.cleanup()
        self.instances = []
        self.running = False
        log.info("Multi-controller stopped")

    def run(self):
        """Run the multi-controller"""
        log.info("Multi-Controller Started")
        try:
            while not (self.hkmgr.should_exit or self.stop_event.is_set()):
                if self.hkmgr.running and not self.running:
                    self.on_start()
                elif not self.hkmgr.running and self.running:
                    self.on_stop()

                if self.running:
                    self._main_loop_iteration()

                time.sleep(1)  # Slow down loop
        except KeyboardInterrupt:
            log.info("Multi-controller interrupted by user")
        except Exception as e:
            log.error(f"Unexpected error in Multi-controller: {e}")
            log.error(traceback.format_exc())
        finally:
            self.on_stop()
            log.info("Multi-controller exited")

    def _main_loop_iteration(self):
        """Handle multi iteration of the loop"""
        for inst in self.instances:
            if not inst.initialized or inst.event_stop.is_set():
                continue

            try:
                # Check if to stop
                if self.stop_event.is_set() or not self.hkmgr.running:
                    break

                # Capture screen
                if inst.wdmgr is None:
                    continue
                screen = inst.wdmgr.capture_screen()

                # Template matching
                if inst.alctr is None:
                    continue
                match = inst.alctr.match_template(screen)
                name = match.name

                # Process game state
                self._process_game_state(inst, name, match)

            except Exception:
                log.error(f"Error in main loop iteration processing instance {inst.idx}")
                log.error(traceback.format_exc())

    def _process_game_state(self, instance: GameInstance, state_name: str, match: Match):
        """Process game state and take appropriate actions"""
        if instance.event_stop.is_set():
            return

        if state_name in ["battle_loading", "battle_queue", "battle_mission",
                          "battle_member", "battle_tips"]:
            self._handle_battle_preparation(instance)

        elif state_name in ["battle_began", "map_mode", "b_btn", "autopilot_on"]:
            self._handle_battle_start(instance, match)

        elif state_name in ["shift_btn", "f1_btn", "back_to_port_btn_2"]:
            self._handle_battle_end(instance)

        else:
            self._handle_port_state(instance, match)

    def _handle_battle_preparation(self, instance: GameInstance):
        """Handle states when battle is loading or in queue"""
        if not instance.in_battle:
            log.info(f"Instance {instance.idx} waiting for battle to start")
        instance.in_battle = True

    def _handle_battle_start(self, instance: GameInstance, match):
        """Handle the start of a battle"""
        if not instance.in_battle:
            log.info(f"Instance {instance.idx} Battle started")
        instance.in_battle = True
        if instance.battlebot:
            instance.battlebot.tick(match=match)

    def _handle_battle_end(self, instance: GameInstance):
        """Handle the end of a battle"""
        if instance.in_battle:
            log.info(f"Instance {instance.idx} Battle ended")
        instance.in_battle = False
        if instance.battlebot:
            instance.battlebot.quit_battle()
        instance.task_manager.record_battle()

        # Check if we've finished all scheduled tasks
        if instance.task_manager.is_finished_all_tasks():
            log.info(f"Instance {instance.idx} all scheduled tasks completed, stopping")
            instance.event_stop.set()

    def _handle_port_state(self, instance: GameInstance, match):
        """Handle being in the port/harbor"""
        # Only log if we're transitioning from battle to port
        if instance.in_battle:
            log.info(f"Instance {instance.idx} returned to port")
        instance.in_battle = False
        if instance.portbot:
            instance.portbot.tick(match=match)
