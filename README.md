# WoWsBot

[English](#english) | [简体中文](#简体中文)

---

## English

**WoWsBot** is a modular automation script for the online game *World of Warships*. It uses **template matching**, **OCR**, and **YOLO models** to recognize game states (e.g., in port, in battle) and automatically performs actions like entering battle or managing combat scenarios.

This project is designed with a clear, component-based architecture for easy customization and extension.

> ⚠️ **Disclaimer**: This bot is for **educational and research purposes only**. Using automation software in online games may violate the game's Terms of Service and can result in account suspension. Use at your own risk.

### Features
- **Hotkey Control**: Start/stop with `F10`/`F11`.
- **Window Management**: Automatically sets the game window to borderless mode at a specified resolution.
- **Advanced State Detection**: Uses image template matching, OCR, and YOLO models to identify game UI elements and game states.
- **Modular Design**: Separates logic into `MainController`, `HotkeyManager`, `AreaLocator`, `Bot`, and other modules.
- **Configurable**: All templates, areas, and thresholds are defined in `config.json`.
- **Scheduled Tasks**: Support for scheduling automated tasks during specific time periods.
- **GUI Interface**: User-friendly graphical interface for monitoring and configuration.
- **Gameplay Automation**: Supports both port operations and in-battle behaviors.

### Prerequisites
- Python 3.12 or higher
- Windows operating system (due to Windows-specific libraries)
- World of Warships installed and configured

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/wowsbot.git
cd wowsbot
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure the bot by modifying `resources/config.json` and `resources/user.json`.

4. Prepare template images and region settings according to your game resolution.

### Quick Start
1. Ensure World of Warships is installed and can run on your system.
2. Configure the game to run in windowed mode with a fixed resolution.
3. Update the `region` and template images in the `resources/` folder to match your setup.
4. Run the script:
```bash
python main.py
```
5. Press `F10` to start and `F11` to stop the automation.

### Architecture Overview
- [`main.py`](file:///d:/Documents/Projects/WoWsBot/main.py): Entry point of the application
- [`src/HkMgr.py`](file:///d:/Documents/Projects/WoWsBot/src/HkMgr.py): Hotkey management
- [`src/MCtrl.py`](file:///d:/Documents/Projects/WoWsBot/src/MCtrl.py): Main controller coordinating different modules
- [`src/ArLctr.py`](file:///d:/Documents/Projects/WoWsBot/src/ArLctr.py): Area locator for identifying screen regions
- [`src/Bot.py`](file:///d:/Documents/Projects/WoWsBot/src/Bot.py): Bot behaviors for in-port and in-battle actions
- [`src/GUI.py`](file:///d:/Documents/Projects/WoWsBot/src/GUI.py): Graphical user interface
- [`src/WinMgr.py`](file:///d:/Documents/Projects/WoWsBot/src/WinMgr.py): Window management utilities
- [`resources/config.json`](file:///d:/Documents/Projects/WoWsBot/resources/config.json): Configuration file for detection areas and parameters
- [`resources/user.json`](file:///d:/Documents/Projects/WoWsBot/resources/user.json): User preferences and scheduled tasks

### License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for details.

---

## 简体中文

**WoWsBot** 是一款为网络游戏《战舰世界》设计的模块化自动化脚本。它通过**模板匹配**、**OCR**技术和**YOLO模型**识别游戏状态（例如：在港口、在战斗中），并自动执行诸如进入战斗等操作。

本项目采用清晰的组件化架构，便于自定义和扩展。

> ⚠️ **免责声明**：本工具仅用于**学习和研究目的**。在在线游戏中使用自动化软件可能违反游戏服务条款，并导致账号被封禁。使用风险自负。

### 主要功能
- **热键控制**：按 `F10` 启动，`F11` 暂停。
- **窗口管理**：自动将游戏窗口设置为无边框模式，并调整至指定分辨率。
- **高级状态识别**：通过图像模板匹配、OCR和YOLO模型识别游戏内的UI元素和游戏状态。
- **模块化设计**：逻辑分离，包含 `MainController`、`HotkeyManager`、`AreaLocator`、`Bot` 等模块。
- **高度可配置**：所有模板、区域和阈值均在 `config.json` 文件中定义。
- **定时任务**：支持在特定时间段内执行自动化任务。
- **图形界面**：友好的用户界面用于监控和配置。
- **游戏自动化**：支持港口操作和战斗内行为。

### 环境要求
- Python 3.12 或更高版本
- Windows 操作系统（由于使用了Windows特定的库）
- 已安装并配置好的战舰世界游戏

### 安装步骤
1. 克隆代码仓库：
```bash
git clone https://github.com/yourusername/wowsbot.git
cd wowsbot
```

2. 安装依赖：
```bash
pip install -e .
```

3. 通过修改 `resources/config.json` 和 `resources/user.json` 来配置机器人。

4. 根据您的游戏分辨率准备模板图像和区域设置。

### 快速开始
1. 确保战舰世界已安装且能在您的系统上正常运行。
2. 将游戏配置为固定分辨率的窗口模式。
3. 根据你的屏幕设置，更新 `resources/` 文件夹中的 `region` 参数和模板图片。
4. 运行脚本：
```bash
python main.py
```
5. 按下 `F10` 键来启动，按下 `F11` 键来暂停自动化。

### 架构概述
- [`main.py`](file:///d:/Documents/Projects/WoWsBot/main.py): 应用程序入口点
- [`src/HkMgr.py`](file:///d:/Documents/Projects/WoWsBot/src/HkMgr.py): 热键管理
- [`src/MCtrl.py`](file:///d:/Documents/Projects/WoWsBot/src/MCtrl.py): 主控制器，协调各个模块
- [`src/ArLctr.py`](file:///d:/Documents/Projects/WoWsBot/src/ArLctr.py): 区域定位器，用于识别屏幕区域
- [`src/Bot.py`](file:///d:/Documents/Projects/WoWsBot/src/Bot.py): 机器人行为，包括港口和战斗中的操作
- [`src/GUI.py`](file:///d:/Documents/Projects/WoWsBot/src/GUI.py): 图形用户界面
- [`src/WinMgr.py`](file:///d:/Documents/Projects/WoWsBot/src/WinMgr.py): 窗口管理工具
- [`resources/config.json`](file:///d:/Documents/Projects/WoWsBot/resources/config.json): 检测区域和参数的配置文件
- [`resources/user.json`](file:///d:/Documents/Projects/WoWsBot/resources/user.json): 用户偏好设置和定时任务

### 开源许可
本项目采用 **GNU General Public License v3.0 (GPL-3.0)** 开源许可证。详情请见 [LICENSE](LICENSE) 文件。