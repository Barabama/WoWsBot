# src/bot/input.py

import ctypes
from ctypes import wintypes
from enum import IntEnum
from typing import Any


class SendType(IntEnum):
    AnyDriver = 0
    SendInput = 1
    Logitech = 2
    LogitechGHubNew = 6
    Razer = 3
    DD = 4
    MouClassInputInjection = 5


class MoveMode(IntEnum):
    Absolute = 0
    Relative = 1


class VirtualKeys(IntEnum):
    # Mouse buttons
    LBUTTON = 0x01
    RBUTTON = 0x02
    CANCEL = 0x03
    MBUTTON = 0x04
    XBUTTON1 = 0x05
    XBUTTON2 = 0x06
    # 0x07: reserved
    
    # Basic keys
    BACKSPACE = 0x08
    TAB = 0x09

    # 0x0A - 0x0B: reserved

    CLEAR = 0x0C
    RETURN = 0x0D
    ENTER = 0x0D
    SHIFT = 0x10
    CONTROL = 0x11
    CTRL = 0x11
    MENU = 0x12
    ALT = 0x12
    PAUSE = 0x13
    CAPITAL = 0x14
    CAPSLOCK = 0x14

    # Language keys
    KANA = 0x15
    HANGEUL = 0x15
    HANGUL = 0x15
    # 0x16: unassigned
    JUNJA = 0x17
    FINAL = 0x18
    HANJA = 0x19
    KANJI = 0x19
    # 0x1A: unassigned

    ESCAPE = 0x1B
    ESC = 0x1B
    CONVERT = 0x1C
    NONCONVERT = 0x1D
    ACCEPT = 0x1E
    MODECHANGE = 0x1F
    
    SPACE = 0x20
    PRIOR = 0x21
    PAGEUP = 0x21
    NEXT = 0x22
    PAGEDOWN = 0x22
    END = 0x23
    HOME = 0x24
    LEFT = 0x25
    UP = 0x26
    RIGHT = 0x27
    DOWN = 0x28
    SELECT = 0x29
    PRINT = 0x2A
    EXECUTE = 0x2B
    SNAPSHOT = 0x2C
    INSERT = 0x2D
    DELETE = 0x2E
    HELP = 0x2F
    
    # Numberic
    KEY_0 = 0x30
    KEY_1 = 0x31
    KEY_2 = 0x32
    KEY_3 = 0x33
    KEY_4 = 0x34
    KEY_5 = 0x35
    KEY_6 = 0x36
    KEY_7 = 0x37
    KEY_8 = 0x38
    KEY_9 = 0x39

    # 0x3A - 0x40: unassigned
    
    # Letters
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A
    
    # Windows
    LWIN = 0x5B
    RWIN = 0x5C
    APPS = 0x5D
    # 0x5E: reserved
    SLEEP = 0x5F
    
    # Numeric
    NUMPAD0 = 0x60
    NUMPAD1 = 0x61
    NUMPAD2 = 0x62
    NUMPAD3 = 0x63
    NUMPAD4 = 0x64
    NUMPAD5 = 0x65
    NUMPAD6 = 0x66
    NUMPAD7 = 0x67
    NUMPAD8 = 0x68
    NUMPAD9 = 0x69
    MULTIPLY = 0x6A
    ADD = 0x6B
    SEPARATOR = 0x6C
    SUBTRACT = 0x6D
    DECIMAL = 0x6E
    DIVIDE = 0x6F
    
    # Functions
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B
    F13 = 0x7C
    F14 = 0x7D
    F15 = 0x7E
    F16 = 0x7F
    F17 = 0x80
    F18 = 0x81
    F19 = 0x82
    F20 = 0x83
    F21 = 0x84
    F22 = 0x85
    F23 = 0x86
    F24 = 0x87
    
    # Navigations
    NAVIGATION_VIEW = 0x88
    NAVIGATION_MENU = 0x89
    NAVIGATION_UP = 0x8A
    NAVIGATION_DOWN = 0x8B
    NAVIGATION_LEFT = 0x8C
    NAVIGATION_RIGHT = 0x8D
    NAVIGATION_ACCEPT = 0x8E
    NAVIGATION_CANCEL = 0x8F
    
    NUMLOCK = 0x90
    SCROLL = 0x91
    
    # OEM
    OEM_NEC_EQUAL = 0x92
    OEM_FJ_JISHO = 0x92
    OEM_FJ_MASSHOU = 0x93
    OEM_FJ_TOUROKU = 0x94
    OEM_FJ_LOYA = 0x95
    OEM_FJ_ROYA = 0x96

    # 0x97 - 0x9F: unassigned
    
    # Left/Right
    LSHIFT = 0xA0
    RSHIFT = 0xA1
    LCONTROL = 0xA2
    RCONTROL = 0xA3
    LMENU = 0xA4
    RMENU = 0xA5
    
    # Browsers
    BROWSER_BACK = 0xA6
    BROWSER_FORWARD = 0xA7
    BROWSER_REFRESH = 0xA8
    BROWSER_STOP = 0xA9
    BROWSER_SEARCH = 0xAA
    BROWSER_FAVORITES = 0xAB
    BROWSER_HOME = 0xAC
    
    # Medias
    VOLUME_MUTE = 0xAD
    VOLUME_DOWN = 0xAE
    VOLUME_UP = 0xAF
    MEDIA_NEXT_TRACK = 0xB0
    MEDIA_PREV_TRACK = 0xB1
    MEDIA_STOP = 0xB2
    MEDIA_PLAY_PAUSE = 0xB3
    LAUNCH_MAIL = 0xB4
    LAUNCH_MEDIA_SELECT = 0xB5
    LAUNCH_APP1 = 0xB6
    LAUNCH_APP2 = 0xB7

    # 0xB8 - 0xB9: reserved
    
    # Specials
    OEM_1 = 0xBA          # ;: for US
    OEM_PLUS = 0xBB       # +
    OEM_COMMA = 0xBC      # ,
    OEM_MINUS = 0xBD      # -
    OEM_PERIOD = 0xBE     # .
    OEM_2 = 0xBF          # /? for US
    OEM_3 = 0xC0          # `~ for US

    # 0xC1 - 0xC2: reserved
    
    # Gamepads
    GAMEPAD_A = 0xC3             # reserved
    GAMEPAD_B = 0xC4             # reserved
    GAMEPAD_X = 0xC5             # reserved
    GAMEPAD_Y = 0xC6             # reserved
    GAMEPAD_RIGHT_SHOULDER = 0xC7 # reserved
    GAMEPAD_LEFT_SHOULDER = 0xC8  # reserved
    GAMEPAD_LEFT_TRIGGER = 0xC9   # reserved
    GAMEPAD_RIGHT_TRIGGER = 0xCA  # reserved
    GAMEPAD_DPAD_UP = 0xCB        # reserved
    GAMEPAD_DPAD_DOWN = 0xCC      # reserved
    GAMEPAD_DPAD_LEFT = 0xCD      # reserved
    GAMEPAD_DPAD_RIGHT = 0xCE     # reserved
    GAMEPAD_MENU = 0xCF           # reserved
    GAMEPAD_VIEW = 0xD0           # reserved
    GAMEPAD_LEFT_THUMBSTICK_BUTTON = 0xD1  # reserved
    GAMEPAD_RIGHT_THUMBSTICK_BUTTON = 0xD2 # reserved
    GAMEPAD_LEFT_THUMBSTICK_UP = 0xD3      # reserved
    GAMEPAD_LEFT_THUMBSTICK_DOWN = 0xD4    # reserved
    GAMEPAD_LEFT_THUMBSTICK_RIGHT = 0xD5   # reserved
    GAMEPAD_LEFT_THUMBSTICK_LEFT = 0xD6    # reserved
    GAMEPAD_RIGHT_THUMBSTICK_UP = 0xD7     # reserved
    GAMEPAD_RIGHT_THUMBSTICK_DOWN = 0xD8   # reserved
    GAMEPAD_RIGHT_THUMBSTICK_RIGHT = 0xD9  # reserved
    GAMEPAD_RIGHT_THUMBSTICK_LEFT = 0xDA   # reserved
    
    # OEM
    OEM_4 = 0xDB          # [{ for US
    OEM_5 = 0xDC          # \| for US
    OEM_6 = 0xDD          # ]} for US
    OEM_7 = 0xDE          # '" for US
    OEM_8 = 0xDF

    # 0xE0: reserved
    
    # OEM
    OEM_AX = 0xE1         # AX key on Japanese AX keyboard
    OEM_102 = 0xE2        # "<>" or "\|" on RT 102-key keyboard
    ICO_HELP = 0xE3       # Help key on ICO
    ICO_00 = 0xE4         # 00 key on ICO
    
    # IME
    PROCESSKEY = 0xE5
    
    # 0xE6: VK_ICO_CLEAR
    
    PACKET = 0xE7
    
    # 0xE8: unassigned

    # OEM
    OEM_RESET = 0xE9
    OEM_JUMP = 0xEA
    OEM_PA1 = 0xEB
    OEM_PA2 = 0xEC
    OEM_PA3 = 0xED
    OEM_WSCTRL = 0xEE
    OEM_CUSEL = 0xEF
    OEM_ATTN = 0xF0
    OEM_FINISH = 0xF1
    OEM_COPY = 0xF2
    OEM_AUTO = 0xF3
    OEM_ENLW = 0xF4
    OEM_BACKTAB = 0xF5
    
    # Specials
    ATTN = 0xF6
    CRSEL = 0xF7
    EXSEL = 0xF8
    EREOF = 0xF9
    PLAY = 0xFA
    ZOOM = 0xFB
    NONAME = 0xFC
    PA1 = 0xFD
    OEM_CLEAR = 0xFE


class Error(IntEnum):
    Success = 0
    InvalidArgument = 1
    LibraryNotFound = 2
    LibraryLoadFailed = 3
    LibraryError = 4
    DeviceCreateFailed = 5
    DeviceNotFound = 6
    DeviceOpenFailed = 7


class KeyboardModifiers(ctypes.Structure):
    _fields_ = [
        ("LCtrl", ctypes.c_bool, 1),
        ("LShift", ctypes.c_bool, 1),
        ("LAlt", ctypes.c_bool, 1),
        ("LWin", ctypes.c_bool, 1),
        ("RCtrl", ctypes.c_bool, 1),
        ("RShift", ctypes.c_bool, 1),
        ("RAlt", ctypes.c_bool, 1),
        ("RWin", ctypes.c_bool, 1),
    ]


class IbInputSimulator:
    def __init__(
        self,
        libpath: str = "",
        send_type: SendType = SendType.AnyDriver,
        flags: int = 0,
        argument: Any = None,
    ):

        self.lib = ctypes.WinDLL(libpath) if libpath else None
        if not self.lib:
            raise RuntimeError("Input simulation library not found.")
        self.set_functions()
        self.initialized = False
        error_code = self.IbSendInit(send_type, flags, argument)
        if error_code != Error.Success:
            raise RuntimeError("Input simulation library initialization failed.")
        self.initialized = True

    def __del__(self):
        if self.initialized:
            self.IbSendDestroy()

    def set_functions(self):

        # Initialize function
        self.IbSendInit = self.lib.IbSendInit
        self.IbSendInit.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.IbSendInit.restype = ctypes.c_uint32

        # Destroy function
        self.IbSendDestroy = self.lib.IbSendDestroy
        self.IbSendDestroy.argtypes = []
        self.IbSendDestroy.restype = None

        # Mouse move function
        self.IbSendMouseMove = self.lib.IbSendMouseMove
        self.IbSendMouseMove.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        self.IbSendMouseMove.restype = ctypes.c_bool

        # Mouse click function
        self.IbSendMouseClick = self.lib.IbSendMouseClick
        self.IbSendMouseClick.argtypes = [ctypes.c_uint32]
        self.IbSendMouseClick.restype = ctypes.c_bool

        # Mouse wheel function
        self.IbSendMouseWheel = self.lib.IbSendMouseWheel
        self.IbSendMouseWheel.argtypes = [ctypes.c_int32]
        self.IbSendMouseWheel.restype = ctypes.c_bool

        # Keyboard key down function
        self.IbSendKeybdDown = self.lib.IbSendKeybdDown
        self.IbSendKeybdDown.argtypes = [ctypes.c_uint16]
        self.IbSendKeybdDown.restype = ctypes.c_bool

        # Keyboard key up function
        self.IbSendKeybdUp = self.lib.IbSendKeybdUp
        self.IbSendKeybdUp.argtypes = [ctypes.c_uint16]
        self.IbSendKeybdUp.restype = ctypes.c_bool

        # Keyboard key down and up function
        self.IbSendKeybdDownUp = self.lib.IbSendKeybdDownUp
        self.IbSendKeybdDownUp.argtypes = [ctypes.c_uint16, KeyboardModifiers]
        self.IbSendKeybdDownUp.restype = ctypes.c_bool

        # API 2 functions
        self.IbSend_mouse_event = self.lib.IbSend_mouse_event
        self.IbSend_mouse_event.argtypes = [
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_ulonglong,
        ]
        self.IbSend_mouse_event.restype = None

        self.IbSend_keybd_event = self.lib.IbSend_keybd_event
        self.IbSend_keybd_event.argtypes = [
            ctypes.c_byte,
            ctypes.c_byte,
            wintypes.DWORD,
            ctypes.c_ulonglong,
        ]
        self.IbSend_keybd_event.restype = None

    def move_mouse(self, x, y, mode: MoveMode = MoveMode.Absolute) -> bool:
        """
        Move mouse.

        Args:
            x: X coordinate or relative distance
            y: Y coordinate or relative distance
            mode: MoveMode.Absolute or MoveMode.Relative
        Returns:
            bool: True if successful, False otherwise
        """
        return self.IbSendMouseMove(x, y, mode)

    def click_mouse(self, button: VirtualKeys = VirtualKeys.LBUTTON) -> bool:
        """
        Click mouse button.

        Args:
            button: VirtualKeys enum value
        Returns:
            bool: True if successful, False otherwise
        """
        return self.IbSendMouseClick(button)

    def mouse_wheel(self, delta: int) -> bool:
        """
        Scroll mouse wheel.

        Args:
            delta: Scroll amount (positive for up, negative for down)
        Returns:
            bool: True if successful, False otherwise
        """
        return self.IbSendMouseWheel(delta)

    def key_down(self, key: int) -> bool:
        """
        Press a key.

        Args:
            key: Keyboard key code
        Returns:
            bool: True if successful, False otherwise
        """
        return self.IbSendKeybdDown(key)

    def key_up(self, key: int) -> bool:
        """
        Release a key.

        Args:
            key: Keyboard key code
        Returns:
            bool: True if successful, False otherwise
        """
        return self.IbSendKeybdUp(key)

    def press_key(self, key: int, modifiers: KeyboardModifiers | None = None) -> bool:
        """
        Press and release a key with optional modifiers.

        Args:
            key: Keyboard key code
            modifiers: KeyboardModifiers structure
        Returns:
            bool: True if successful, False otherwise
        """
        if modifiers is None:
            modifiers = KeyboardModifiers()
        return self.IbSendKeybdDownUp(key, modifiers)

    def mouse_event(self, flags: int, x: int, y: int, data: int, extra_info: int):
        """
        Low-level mouse event.

        Args:
            flags: Mouse event flags
            x: X coordinate
            y: Y coordinate
            data: Additional data
            extra_info: Extra information
        """
        self.IbSend_mouse_event(flags, x, y, data, extra_info)

    def keybd_event(self, key: int, scan_code: int, flags: int, extra_info: int):
        """
        Low-level keyboard event.

        Args:
            key: Keyboard key code
            scan_code: Scan code
            flags: Keyboard event flags
            extra_info: Extra information
        """
        self.IbSend_keybd_event(key, scan_code, flags, extra_info)