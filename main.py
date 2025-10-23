# main.py

import logging
import sys
import threading
import tkinter as tk
import traceback

from src.HkMgr import HotkeyManager
from src.GUI import MainGUI
from src.MCtrl import MainController


def main():
    hkmgr = HotkeyManager()
    root = tk.Tk()
    gui = MainGUI(root=root, hkmgr=hkmgr, level=log_level)
    root.protocol("WM_DELETE_WINDOW", gui.on_closing)
    try:
        mctrl = MainController(hkmgr=hkmgr)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    thread_hkmgr = threading.Thread(target=hkmgr.start_listener, daemon=True)
    thread_hkmgr.start()

    logging.getLogger(__name__).info("App started.")

    thread_mctrl = threading.Thread(target=mctrl.run, daemon=True)
    thread_mctrl.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("App stopped.")
        hkmgr.script_exit()
        sys.exit(0)
    finally:
        if thread_hkmgr.is_alive():
            thread_hkmgr.join(timeout=0)
        if thread_mctrl.is_alive():
            thread_mctrl.join(timeout=0)


if __name__ == "__main__":
    log_level = "DEBUG" if len(sys.argv) > 1 else "INFO"
    main()
