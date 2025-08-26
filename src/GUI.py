# src/GUI.py

import logging
import tkinter as tk
from tkinter import scrolledtext

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
        self.setup_window()
        self.create_widgets()
        self.setup_logging(level)
        
    def setup_window(self):
        self.root.title("WoWs Bot Controller")
        self.root.geometry("480x480+1440+0")
        self.root.resizable(True, True)
    
    def create_widgets(self):
        # buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_stop_btn = tk.Button(button_frame, text="Start/Stop(F10)", 
                                        command=self.hkmgr.toggle_script)
        self.start_stop_btn.pack(side=tk.LEFT, padx=5)
        
        # logging
        label_log = tk.Label(self.root, text="Runtime Log:")
        label_log.pack(anchor="w", padx=10)
        self.text_log = scrolledtext.ScrolledText(self.root, state="disabled", height=20)
        self.text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_logging(self, level: str="INFO"):
        handler = TextHandler(self.text_log)
        formatter = logging.Formatter("<%(asctime)s>[%(name)s](%(levelname)s):\n%(message)s")
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)
        
        log = logging.getLogger(__name__)
        log.info("GUI Initialized")
        log.info("Press F10 to start/stop the bot")