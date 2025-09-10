# main.py

import logging
import sys
import threading
import tkinter as tk
import traceback

from src.ArLctr import AreaLocator
from src.HkMgr import HotkeyManager
from src.GUI import MainGUI
from src.WinMgr import WindowManager
from src.MCtrl import MainController
from src.Bot import BotInPort, BotInBattle


# title = "World of Warships"
log_level = "DEBUG" if len(sys.argv) > 1 else "INFO"


def main():
    hkmgr = HotkeyManager()
    root = tk.Tk()
    gui = MainGUI(root=root, hkmgr=hkmgr, level=log_level)
    try:
        arlctr = AreaLocator()
        title = arlctr.config["title"]
        region = tuple(arlctr.config["region"])
        wdmgr = WindowManager(title=title, region=region)
        portbot = BotInPort(arlctr=arlctr, wdmgr=wdmgr)
        battlebot = BotInBattle(arlctr=arlctr, wdmgr=wdmgr)

        mctrl = MainController(arlctr=arlctr, hkmgr=hkmgr, wdmgr=wdmgr,
                               portbot=portbot, battlebot=battlebot)
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
        thread_hkmgr.


if __name__ == "__main__":
    main()
