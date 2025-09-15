# src/GUI.py

import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import json
import os

from .HkMgr import HotkeyManager


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)

        def append():
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.configure(state=tk.DISABLED)
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)


class MainGUI:
    def __init__(self, root: tk.Tk, hkmgr: HotkeyManager, level: str):
        self.root = root
        self.hkmgr = hkmgr

        self.user_path = "resources/user.json"
        self.scheduled_tasks = {"enabled": False, "tasks": []}
        self.setup_window()

        self.create_widgets()
        self.setup_logging(level)
        self.load_user()
        self.setup_scheduled_tasks()

    def on_closing(self):
        self.save_user()
        self.root.destroy()

    def on_scheduled_tasks_enabled(self):
        self.scheduled_tasks["enabled"] = self.var_scheduled_tasks_enabled.get()

    def get_actual_title(self):
        title = self.entry_title.get().strip()
        return title if title else self.var_title.get()

    def load_user(self):
        try:
            with open(self.user_path, "r", encoding="utf-8") as f:
                user = json.load(f)
            self.var_lang.set(user["language"])

            title = user["title"]
            if title in ["《战舰世界》", "World of Warships"]:
                self.var_title.set(title)
                self.entry_title.delete(0, tk.END)
            else:
                self.var_title.set("")
                self.entry_title.delete(0, tk.END)
                self.entry_title.insert(0, title)

            self.scheduled_tasks = user["scheduled_tasks"]
        except (FileNotFoundError, KeyError):
            self.var_lang.set("zh_cn")
            self.var_title.set("《战舰世界》")
            self.scheduled_tasks = {"enabled": False, "tasks": []}
            self.save_user()

    def save_user(self):
        user = {"language": self.var_lang.get(),
                "title": self.get_actual_title(),
                "scheduled_tasks": self.scheduled_tasks}
        try:
            with open(self.user_path, "w", encoding="utf-8") as f:
                json.dump(user, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_tasks(self):
        self.listbox_tasks.delete(0, tk.END)
        for t in self.scheduled_tasks.get("tasks", []):
            self.listbox_tasks.insert(
                tk.END,
                f"{t['type']} - {t['start']} to {t['end']} ({t['count']} times)"
            )

    def add_task(self):
        win_task = tk.Toplevel(self.root)
        win_task.title("Add Task")
        win_task.geometry("250x400+1500+50")
        win_task.grab_set()
        win_task.focus_set()

        tk.Label(win_task, text="TaskType:").pack(anchor="w", padx=10, pady=5)
        var_type = tk.StringVar(value="daily")
        tk.Radiobutton(win_task, text="DailyTask", variable=var_type, value="daily").pack(anchor="w", padx=20, pady=5)
        tk.Radiobutton(win_task, text="SingleTask", variable=var_type, value="single").pack(anchor="w", padx=20, pady=5)

        tk.Label(win_task, text="StartTime (HH:MM):").pack(anchor="w", padx=10, pady=5)
        var_start = tk.StringVar()
        tk.Entry(win_task, textvariable=var_start).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(win_task, text="EndTime (HH:MM):").pack(anchor="w", padx=10, pady=5)
        var_end = tk.StringVar()
        tk.Entry(win_task, textvariable=var_end).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(win_task, text="BattleCount:").pack(anchor="w", padx=10, pady=5)
        var_count = tk.IntVar(value=10)
        tk.Spinbox(win_task, from_=1, to=99, textvariable=var_count).pack(fill=tk.X, padx=10, pady=5)

        # save task
        def _save_task():
            task = {"type": var_type.get(),
                    "start": var_start.get(),
                    "end": var_end.get(),
                    "count": var_count.get()}
            self.scheduled_tasks["tasks"].append(task)
            self.refresh_tasks()
            win_task.destroy()

        tk.Button(win_task, text="Save", command=_save_task).pack(fill=tk.X, padx=10, pady=10)
        tk.Button(win_task, text="Cancel", command=win_task.destroy).pack(fill=tk.X, padx=10, pady=10)

    def edit_task(self):
        selection = self.listbox_tasks.curselection()
        if not selection:
            return

        idx = selection[0]
        task = self.scheduled_tasks["tasks"][idx]

        win_task = tk.Toplevel(self.root)
        win_task.title("Edit Task")
        win_task.geometry("250x400+1500+50")
        win_task.grab_set()
        win_task.focus_set()

        tk.Label(win_task, text="TaskType:").pack(anchor="w", padx=10, pady=5)
        var_type = tk.StringVar(value="daily")
        tk.Radiobutton(win_task, text="DailyTask", variable=var_type, value="daily").pack(anchor="w", padx=20, pady=5)
        tk.Radiobutton(win_task, text="SingleTask", variable=var_type, value="single").pack(anchor="w", padx=20, pady=5)

        tk.Label(win_task, text="StartTime (HH:MM):").pack(anchor="w", padx=10, pady=5)
        var_start = tk.StringVar()
        tk.Entry(win_task, textvariable=var_start).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(win_task, text="EndTime (HH:MM):").pack(anchor="w", padx=10, pady=5)
        var_end = tk.StringVar()
        tk.Entry(win_task, textvariable=var_end).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(win_task, text="BattleCount:").pack(anchor="w", padx=10, pady=5)
        var_count = tk.IntVar(value=10)
        tk.Spinbox(win_task, from_=1, to=99, textvariable=var_count).pack(fill=tk.X, padx=10, pady=5)

        def _update_task():
            task.update({"type": var_type.get(),
                         "start": var_start.get(),
                         "end": var_end.get(),
                         "count": var_count.get()})
            self.refresh_tasks()
            win_task.destroy()

        tk.Button(win_task, text="Update", command=_update_task).pack(fill=tk.X, padx=10, pady=10)
        tk.Button(win_task, text="Cancel", command=win_task.destroy).pack(fill=tk.X, padx=10, pady=10)

    def remove_task(self):
        selection = self.listbox_tasks.curselection()
        if not selection:
            return

        idx = selection[0]
        del self.scheduled_tasks["tasks"][idx]
        self.refresh_tasks()

    def setup_window(self):
        self.root.title("WoWs Bot Controller")
        self.root.geometry("480x480+1440+0")
        self.root.resizable(True, True)

    def create_widgets(self):
        # notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # main frame
        self.frame_main = tk.Frame(self.notebook)
        self.notebook.add(self.frame_main, text="Main")

        # buttons
        frame_btn = tk.Frame(self.frame_main)
        frame_btn.pack(fill=tk.X, padx=10, pady=5)

        self.btn_start = tk.Button(frame_btn, text="Start(F10)",
                                   command=self.hkmgr.script_start)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(frame_btn, text="Stop(F11)",
                                  command=self.hkmgr.script_stop)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # logging
        label_log = tk.Label(self.frame_main, text="Runtime Log:")
        label_log.pack(anchor="w", padx=10)
        self.text_log = scrolledtext.ScrolledText(self.frame_main, state="disabled", height=20)
        self.text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # uesr
        self.frame_user = tk.Frame(self.notebook)
        self.notebook.add(self.frame_user, text="User")
        self.create_user_widgets()

        # tasks
        self.frame_scheduled_tasks = tk.Frame(self.notebook)
        self.notebook.add(self.frame_scheduled_tasks, text="Tasks")
        self.create_scheduled_tasks_widgets()

    def create_user_widgets(self):
        tk.Label(self.frame_user, text="UserConfig", font=("Arial", 12, "bold")).pack(pady=10)

        # language
        tk.Label(self.frame_user, text="Language:").pack(anchor="w", padx=10, pady=5)
        self.var_lang = tk.StringVar()
        combo_lang = ttk.Combobox(self.frame_user, textvariable=self.var_lang,
                                  values=["zh_cn", "en_us"])
        combo_lang.pack(anchor="w", padx=10, pady=5)

        # title
        tk.Label(self.frame_user, text="GameTitle:").pack(anchor="w", padx=10, pady=5)
        self.var_title = tk.StringVar()
        combo_title = ttk.Combobox(self.frame_user, textvariable=self.var_title)
        combo_title["values"] = ("《战舰世界》", "World of Warships")
        combo_title.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(self.frame_user, text="Custom Title (if not in above list):").pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_title = tk.Entry(self.frame_user)
        self.entry_title.pack(fill=tk.X, padx=10, pady=5)

        # save
        tk.Button(self.frame_user, text="Save", command=self.save_user).pack(pady=20)

    def create_scheduled_tasks_widgets(self):
        tk.Label(self.frame_scheduled_tasks, text="ScheduledTasks", font=("Arial", 12, "bold")).pack(pady=10)

        self.var_scheduled_tasks_enabled = tk.BooleanVar()
        check_enabled = tk.Checkbutton(self.frame_scheduled_tasks, text="Enabled", variable=self.var_scheduled_tasks_enabled,
                                       command=self.on_scheduled_tasks_enabled)
        check_enabled.pack(anchor="w", padx=10, pady=5)

        # tasks frame
        frame_tasks = tk.LabelFrame(self.frame_scheduled_tasks, text="Tasks")
        frame_tasks.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # tasks listbox
        self.listbox_tasks = tk.Listbox(frame_tasks)
        self.listbox_tasks.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # scrollbar
        scrollbar = tk.Scrollbar(frame_tasks, command=self.listbox_tasks.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_tasks.config(yscrollcommand=scrollbar.set)

        # task btns
        frame_task_btns = tk.Frame(self.frame_scheduled_tasks)
        frame_task_btns.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(frame_task_btns, text="AddTask", command=self.add_task).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_task_btns, text="EditTask", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_task_btns, text="RemoveTask", command=self.remove_task).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_task_btns, text="SaveTasks", command=self.save_user).pack(side=tk.LEFT, padx=5)

        self.refresh_tasks()
        self.var_scheduled_tasks_enabled.set(self.scheduled_tasks.get("enabled", False))

    def setup_logging(self, level: str = "INFO"):
        handler = TextHandler(self.text_log)
        formatter = logging.Formatter("<%(asctime)s>[%(name)s](%(levelname)s):\n%(message)s")
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)

        log = logging.getLogger(__name__)
        log.info("GUI Initialized")
        log.info("Press F10 to start, F11 to stop")

    def setup_scheduled_tasks(self):
        pass
