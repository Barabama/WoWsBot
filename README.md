# WoWsBot

[English](#english) | [简体中文](#简体中文)

---

## English

**WoWsBot** is a modular automation script for the online game *World of Warships*. It uses **template matching** and **OCR** to recognize game states (e.g., in port, in battle) and automatically performs actions like entering battle or managing combat scenarios.

This project is designed with a clear, component-based architecture for easy customization and extension.

> ⚠️ **Disclaimer**: This bot is for **educational and research purposes only**. Using automation software in online games may violate the game's Terms of Service and can result in account suspension. Use at your own risk.

### Features
- **Hotkey Control**: Start/stop with `F10`.
- **Window Management**: Automatically sets the game window to borderless mode at a specified resolution.
- **State Detection**: Uses image template matching to identify game UI elements (e.g., "Start Battle" button).
- **Modular Design**: Separates logic into `MainController`, `HotkeyManager`, `AreaLocator`, and `Bot` modules.
- **Configurable**: All templates, areas, and thresholds are defined in `config.json`.

### Quick Start
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Place your game window at the correct position and ensure it's in windowed mode.
3. Update the `region` and template images in the `resources/` folder to match your setup.
4. Run the script:
```bash
python main.py
```
5. Press `F10` to start/stop the automation.

### License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for details.

---

## 简体中文

**WoWsBot** 是一款为网络游戏《战舰世界》设计的模块化自动化脚本。它通过**模板匹配**和**OCR**技术识别游戏状态（例如：在港口、在战斗中），并自动执行诸如进入战斗等操作。

本项目采用清晰的组件化架构，便于自定义和扩展。

> ⚠️ **免责声明**：本工具仅用于**学习和研究目的**。在在线游戏中使用自动化软件可能违反游戏服务条款，并导致账号被封禁。使用风险自负。

### 主要功能
- **热键控制**：按 `F10` 启动/暂停。
- **窗口管理**：自动将游戏窗口设置为无边框模式，并调整至指定分辨率。
- **状态识别**：通过图像模板匹配识别游戏内的UI元素（如“开始战斗”按钮）。
- **模块化设计**：逻辑分离，包含 `MainController`、`HotkeyManager`、`AreaLocator` 和 `Bot` 等模块。
- **高度可配置**：所有模板、区域和阈值均在 `config.json` 文件中定义。

### 快速开始
1. 安装依赖：
```bash
pip install -r requirements.txt
```
2. 将游戏窗口放置在正确位置，并确保其处于窗口化模式。
3. 根据你的屏幕设置，更新 `resources/` 文件夹中的 `region` 参数和模板图片。
4. 运行脚本：
```bash
python main.py
```
5. 按下 `F10` 键来启动或暂停自动化。

### 开源许可
本项目采用 **GNU General Public License v3.0 (GPL-3.0)** 开源许可证。详情请见 [LICENSE](LICENSE) 文件。
