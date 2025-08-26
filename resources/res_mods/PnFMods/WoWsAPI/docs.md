

# battle

Battle methods are only available in battle
We need to use `events.onSFMEvent` to manage the event

```python2

def SFMEvent(eventName, eventData):
    if eventName == 'window.show' and eventData['windowName'] =='Battle':
        PlayersInfo = battle.getPlayersInfo()
        with open('test.log', 'a') as f:
            f.write('<{}> EventName: {}, EventData: {}\n'.format(utils.timeNow(), enventName, eventData))

events.onSFMEvent(SFMEvent)
```

- `battle.getPlayersInfo()` returns dict{PlayerID: PlayerInfo}

- `battle.getPlayerInfo(playerID)` input playerID, return dict of playerInfo

- `battle.getSelfPlayerInfo()` return dict of self playerInfo

- `battle.getPlayersInfoByName(name)` input player's name, return dict of playerInfo

- `battle.getPlayerShipInfo(playerID)` input playerID, return dict of shipInfo

- `battle.getPlayerByVehicleId(shipID)` input shipID, return dict of playerInfo

- `battle.getAmmoParams(ammoID)` input ammoID gotten from `events.onReceiveShellInfo`, 
  return dict of ammoInfo

- `battle.isVehicleBurning(shipID)` input shipID, return True if burning, use in
  `events.onReceiveShellInfo`

- `battle.isVehicleFloating(shipID)` input shipID, return True if floating, like 
  `battle.isVehicleBurning`

- `battle.isBattleStarted()` return True if battle started



# Callbacks

Callbacks fucntions are designed to repeatly call functions

- `callbacks.perTick(func)` call func every tick of game, return handle a unique id
  It may cause a decrease in performance of the game client

```python2
counter = 0
def func():
    global counter
    with open('test_callbacks.txt', 'a') as f:
        f.write(str(counter))
        counter += 1

with open('test_callbacks.txt', 'w') as f:
    handlePerTick = callbacks.perTick(func)
    f.write('{}\n'.format(handlePerTick))
# e.g. 
# hanldePerTick = '''1455164848
# 012345678910111213
# ...
```

- `callbacks.callback(delaytime, func, *args, **kwargs)` input delaytime(int, /s)
  and func(*args, **kwargs), return handle

- `callbacks.cancel(handle)` cancel callback

# events

Events are allow you to manager events like opening window, clicking button,
pressing key, being in battle, etc.

- `events.onFlash(func)` immediately call func() as loading `Main.swf`

- `events.onSFMEvent(func)` func needs two arguments: eventName(str) and eventData(dict)

```python2
def event(eventName, eventData):
    with open('test_events.log', 'a') as f:
        f.wirite('EventName: {}\nEventData: {}\n'.format(eventName, eventData))

events.onSFMEvent(event)
```

- `events.onReceiveShellInfo(func)` when inflicting/taking damage to/from the enemy 
  with shells/torpedoes. 
  func(*args, **kwargs) needs 
    victimID(shipID),
    shooterID(shipID),
    ammoID(ammoID),
    matID: materialID,
    shotID: cameraID,
    booleans: damage_types = {
        1: "damage",
        2: "penetration",
        3: "underwater",
        4: "ship_destroyed",
        5: "over_penetration",
        6: "ricochet",
        7: "splash",
        8: "main_gun_destroyed",
        9: "torpedo_launcher_destroyed",
        10: "secondary_battery_destroyed"
    },
    damage: num of damage,
    shotPosition: tuple of pos of hit,
    hlinfo: tuple about shot

- `events.onBattleStart(func)` call when battle starts 

- `events.onBattleEnd(func)` call when battle ends

- `events.onBattleQuit(func)` call when battle quits, fucn neens a True

- `events.onKeyEvent(func)` available when pressing key or clicking mouse
  func(event) needs a object event with properties:
    - event.key: Keys.KEY_F1 - F1, Keys.KEY_Q - Q, etc.
    - event.isKeyDown: True or False
    - event.isKeyUp: True or False
    - event.isShiftDown: True or False
    - event.isCtrlDown: True or False
    - event.isAltDown: True or False

- `events.onMouseEvent(func)` func(event) needs a object event with properties:
    - event.dx: change in x
    - event.dy: change in y
    - event.dz: always 0

- `events.onGotRibbon(func)` func(*args, **kwargs)

- `events.onAchievementEarned(func)` func(*args, **kwargs)

- `events.onBattleStatsRecived(func)` func(arg)

# utils

- `utils.getGameVersion()` return like '0,5,15,123456'

- `utils.getModDir()` return moddir abspath

- `utils.stat(path)` same as os.stat(path)

- `utils.walk(top, topdown=True, followlinks=False)` same as os.walk

- `utils.isFile(path)` return True if path is file
- `utils.isDir(path)` return True if path is dir
- `utils.isPathExists(path)` return True if path exists

- `utils.timeNowUTC()` same as datetime.datetime.utcnow()
- `utils.timeNow()` same as datetime.datetime.now()

- `utils.jsonEncode(s)` like json.dumps(s)
- `utils.jsonDncode(s)` like json.loads(s)

- `utils.logInfo(message='', *arge, **kwargs)` put msg to python.log file

# dock

- dock.getActiveShipId()
此函数返回所选船舶的 ID。

- dock.getShipInfoById(shipID)
此函数返回一个包含有关飞船信息的对象。
shipID 输入参数是所选船舶的 ID。

- dock.getProfileInfo()
此函数返回一个包含玩家个人资料信息的对象。该对象包含玩家飞船的统计数据（获胜百分比）。


# devmenu

“devmenu”方法允许您使用开发人员菜单。

该菜单有两个按钮：

“常量” - 打开/隐藏一些游戏常量的列表：战利品箱的类型、奖励、战斗磁带和伤害
“Reload Mod” - 重新加载模组

- devmenu.enable()

进入端口后，它允许您调出开发人员菜单。

使用键盘快捷键“Ctrl”+“F1”显示/隐藏菜单。

“重新加载模组”按钮重新加载调出菜单的模组。

当调用多个模组的菜单时，“重新加载模组”按钮将重新加载最后加载的调组，该模组会调出该菜单。

- constants

提供对常量值的访问权限。
获取特定常量（例如，积分）的值是通过以下方式完成的： 常量。LootboxType.CREDITS 中。

返回 int（） 类型的值。