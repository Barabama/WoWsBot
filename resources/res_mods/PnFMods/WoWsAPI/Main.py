API_VERSION = "API_v1.0"
MOD_NAME = "WoWsAPI"
MOD_PATH = utils.getModDir()
DATA_PATH = MOD_PATH + "/../../game_data.json"

damage_types = {1: "damaged",
                2: "penetration",
                3: "underwater",
                4: "ship_destroyed",
                5: "over_penetration",
                6: "ricochet",
                7: "splash_damage",
                8: "main_guns_destroyed",
                9: "torpedo_launcher_destroyed",
                10: "secondary_battery_destroyed", }


class Logger:
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, level=1):
        self.level = level
        self.log_path = MOD_PATH + "/runtime.log"
        if level == 0:
            devmenu.enable()

        time = utils.timeNow()
        game_version = utils.getGameVersion()
        with open(self.log_path, "w") as f:
            f.write("GameVersion {}, {}".format(game_version, API_VERSION))
            f.write("{}: Mod {} loaded \n on {}".format(time, MOD_NAME, MOD_PATH))

    def log(self, name, level=1, message=""):
        if level < self.level:
            return
        time = utils.timeNow()
        msg = str(message)
        str_level = self.levels[level]
        utils.logInfo(msg, str_level)
        with open(self.log_path, "a") as f:
            f.write("{}: <{}>[{}]: {} \n".format(time, name, str_level, msg))


class GameData:

    def __init__(self):
        with open(DATA_PATH, "r") as f:
            self.data = utils.jsonDecode(f.read())

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        else:
            return None

    def update(self, key, value):
        self.data[key] = value
        with open(DATA_PATH, "w") as f:
            f.write(utils.jsonEncode(self.data))


class GameStatus:

    def __init__(self, logger, data):
        self.name = self.__class__.__name__
        self.logger = logger
        self.data = data
        self.handle = None  # callback handle of ship dot

        # events.onSFMEvent(self.sfm_event)
        # events.onKeyEvent(self.key_event)
        # events.onMouseEvent(self.mouse_event)
        # events.onBattleStart(self.battle_start)
        # events.onBattleEnd(self.battle_end)
        # events.onBattleQuit(self.battle_quit)
        # events.onReceiveShellInfo(self.receive_shell_info)
        # Not implemented yet
        # events.onGotRibbon(self.got_ribbon)
        # events.onAchievement(self.achievement)
        # events.onBattleStasRecived(self.battle_stas_recived)
        self.logger.log(name=self.name, message="Initialized")

    def _handle_ship_dot(self, ship_id):
        if battle.isVehicleBurning(ship_id) or battle.isVehicleFloating(ship_id):
            self.logger.log(name="DOT", message="Ship under DOT")
            self.data.update(key="ship_dot", value=True)
        else:
            self.data.update(key="ship_dot", value=False)

    def _handle_battle(self):
        players_info = battle.getPlayersInfo()
        self.logger.log(name="Players", message=players_info)
        self.data.update(key="players_info", value=players_info)

        self_info = battle.getSelfPlayerInfo()
        # player_info = str(player_info).replace("<Dummy>:", "")
        self.logger.log(name="SelfInfo", message=self_info)
        self.data.update(key="self_info", value=self_info)

        self_id = self_info["id"]
        ship_info = battle.getPlayerShipInfo(self_id)
        self.logger.log(name="SelfShip", message=ship_info)
        self.data.update(key="ship_ship", value=ship_info)

        if battle.isBattleStarted() and not self.handle:
            ship_id = ship_info["id"]
            self.handle = callbacks.callback(2, self._handle_ship_dot, ship_id)

    def sfm_event(self, event_name, event_data):
        log_msg = "EventName: {} \nEventData: {}".format(event_name, event_data)
        self.logger.log(name="Event", message=log_msg)

        if event_name == "window.show":
            window_name = event_data["windowName"]
            self.data.update(key="window_name", value=window_name)

            if window_name == "battle":
                self._handle_battle()

    def key_event(self, event):
        event_key = {"key": event.Key,
                     "down": event.isKeyDown,
                     "up": event.isKeyUp,
                     "shift": event.isShiftDown,
                     "ctrl": event.isCtrlDown,
                     "alt": event.isAltDown, }
        self.logger.log(name="Key", message=event_key)
        self.data.update("keyboard", event_key)

    def mouse_event(self, event):
        event_mouse = {"dx": event.dx,
                       "dy": event.dy,
                       "dz": event.dz, }
        self.logger.log(name="Mouse", message=event_mouse)
        self.data.update("mouse", event_mouse)

    def battle_start(self):
        self.logger.log(name="Battle", message="Battle Start")
        self.data.update(key="battle_status", value="start")
        self._handle_battle()

    def battle_end(self):
        self.logger.log(name="Battle", message="Battle End")
        self.data.update(key="battle_status", value="end")
        if self.handle:
            callbacks.cancel(self.handle)

    def battle_quit(self, arg):
        self.logger.log(name="Battle", message="Battle Quit with {}".format(arg))
        self.data.update(key="battle_status", value="quit")
        if self.handle:
            callbacks.cancel(self.handle)

    def receive_shell_info(self, *args, **kwargs):
        shell_info = {"victim_id": args[0],
                      "shooter_id": args[1],
                      "ammo_id": (args[2]),
                      "mat_id": args[3],
                      "shoot_id": args[4],
                      "damage_type": [damage_types[i] for i in damage_types.keys()
                                      if (args[5] >> i) & 1],
                      "damage": args[6],
                      "shot_position": list(args[7]),
                      "yaw": args[8],
                      "hlinfo": list(args[9]), }
        self.logger.log(name="Shell", message=shell_info)
        self.data.update(key="shell_info", value=shell_info)


logger = Logger(level=0)
data = GameData()
# game_status = GameStatus(logger=logger, data=data)