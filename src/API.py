
import json
import os
import re
import shutil


class ApiCaller:
    def __init__(self, gamepath: str):
        self.data = None
        self.resource_path = "resources"
        self.modpath = os.path.join(gamepath, "res_mods")
        self.gamepath = gamepath
        if target := self.find_target():
            self.target = os.path.join(target, "res_mods")
        else:
            raise FileNotFoundError("res_mod not found in game path")
        self.data_path = os.path.join(self.target, "game_data.json")

    def find_target(self) -> str | None:
        """Finds the target path in the max num path"""
        num_max = float("-inf")
        target = None

        bin_path = os.path.join(self.gamepath, "bin")
        if not os.path.isdir(bin_path):
            return

        # find max num in folders
        for folder in os.listdir(bin_path):
            folder_path = os.path.join(bin_path, folder)
            if not os.path.isdir(folder_path):
                continue
            num = re.search(r"\d+", folder)
            if not num:
                continue
            num = int(num.group())
            if num > num_max:
                num_max = num
                target = folder_path

        return target

    def deploy_mod(self):
        """deploy mod folder to target"""
        if not os.path.isdir(self.modpath):
            raise FileNotFoundError(f"res_mods not found in {self.modpath}")

        # backup old mods
        if os.path.isdir(self.target):
            self.backup = os.path.join(self.target, "..", "res_mods_backup")
            shutil.copytree(self.target, self.backup)
            shutil.rmtree(self.target)

        # copy mods
        os.makedirs(self.target, exist_ok=True)
        shutil.copytree(self.modpath, self.target)

    def get_data(self) -> dict:
        with open(self.data_path, "r") as f:
            self.data = json.load(f)
        return self.data
