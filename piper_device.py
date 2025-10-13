
import threading
from contextlib import suppress
from dataclasses import dataclass
from typing import Callable, List

from evdev import InputDevice, categorize, ecodes, list_devices, UInput

all_codes = [code for name, code in ecodes.ecodes.items() if name.startswith("KEY_") and name != "KEY_CNT"]
capabilities = {
    ecodes.EV_KEY: all_codes,
}

@dataclass
class PiperEvent:
    device: InputDevice
    button_id: int
    button_name: str
    pressed: bool


class DeviceWatcher(threading.Thread):
    """A thread that monitors a single input device."""

    def __init__(
            self,
            device: InputDevice,
            callback: Callable[[PiperEvent], None],
    ) -> None:
        super().__init__(daemon=True)
        self.device: InputDevice = device
        self.callback: Callable[[PiperEvent], None] = callback
        self._stop_flag = threading.Event()

    def run(self):
        print(f"[{self.device.path}] Started listening ({self.device.name})")
        try:
            for event in self.device.read_loop():
                if self._stop_flag.is_set():
                    break
                if event.type == ecodes.EV_KEY:
                    key = categorize(event)
                    pressed = True if key.keystate == key.key_down else False
                    button_name = str(key.keycode) if not isinstance(key.keycode, list) else "/".join([i for i in key.keycode])
                    piper_event = PiperEvent(
                        device=self.device,
                        button_id=event.code,
                        button_name=button_name,
                        pressed=pressed
                    )
                    self.callback(piper_event)
        except OSError as e:
            print(f"[{self.device.path}] stopped: {e}")

    def stop(self):
        self._stop_flag.set()
        with suppress(Exception):
            self.device.close()

    def __del__(self) -> None:
        self.stop()


class PiperMouse:
    def __init__(self, callback: Callable[[PiperEvent], None],) -> None:
        self.watchers: List[DeviceWatcher] = []
        self.devices: List[InputDevice] = []
        self.callback = callback

        self._initialise_devices()

    def _initialise_devices(self) -> None:
        for path in list_devices():
            dev = InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_KEY not in caps:
                continue
            key_codes = caps[ecodes.EV_KEY]
            # Check only mice with more 3-19 buttons
            if ecodes.BTN_LEFT in key_codes and ecodes.BTN_RIGHT in key_codes and 2 < len(key_codes) < 20:
                print(f"Mouse found: {dev.path} ({dev.name})")
                self.devices.append(dev)
                watcher = DeviceWatcher(dev, self.callback)
                self.watchers.append(watcher)
                watcher.start()

    def __del__(self) -> None:
        for w in self.watchers:
            w.stop()
        print("All mouse watchers stopped.")


class PiperKeyboard:
    virtual_kb_name = "virtual-piper-kb"
    def __init__(self, callback: Callable[[PiperEvent], None],) -> None:
        self.watchers: List[DeviceWatcher] = []
        self.devices: List[InputDevice] = []
        self.callback = callback

        self.virtual_keyboard = UInput(capabilities, name=self.virtual_kb_name)
        self._initialise_devices()

    def press_key(self, code: int, execute: bool = False) -> None:
        self.virtual_keyboard.write(ecodes.EV_KEY, code, 1)
        if execute:
            self.virtual_keyboard.syn()

    def release_key(self, code: int, execute: bool = False) -> None:
        self.virtual_keyboard.write(ecodes.EV_KEY, code, 0)
        if execute:
            self.virtual_keyboard.syn()

    def click_key(self, code: int, execute: bool = False) -> None:
        self.press_key(code, execute=False)
        self.release_key(code, execute=execute)

    def type_string(self, text: str) -> None:
        sequence = self.text_to_ecodes(text)
        for item in sequence:
            if isinstance(item, tuple):
                for key in item:
                    self.press_key(key)
                for key in reversed(item):
                    self.release_key(key)
            else:
                self.click_key(item)
        self.virtual_keyboard.syn()

    def _initialise_devices(self) -> None:
        for path in list_devices():
            dev = InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_KEY not in caps:
                continue
            key_codes = caps[ecodes.EV_KEY]
            # Check only mice with more 3-19 buttons
            if ecodes.KEY_C in key_codes and ecodes.KEY_V in key_codes and len(key_codes) > 40:
                print(f"Keyboard found: {dev.path} ({dev.name})")
                self.devices.append(dev)
                watcher = DeviceWatcher(dev, self.callback)
                self.watchers.append(watcher)
                watcher.start()

    @staticmethod
    def text_to_ecodes(text: str) -> list[int]:
        """
        Convert text string into a list of evdev key codes.
        Example: 'Hello World!' → [KEY_LEFTSHIFT, KEY_H, KEY_E, KEY_L, ...]
        """
        mapping = {
            " ": ecodes.KEY_SPACE,
            "\n": ecodes.KEY_ENTER,
            ".": ecodes.KEY_DOT,
            ",": ecodes.KEY_COMMA,
            "!": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_1),
            "?": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_SLASH),
            ":": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_SEMICOLON),
            ";": ecodes.KEY_SEMICOLON,
            "'": ecodes.KEY_APOSTROPHE,
            "\"": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_APOSTROPHE),
            "-": ecodes.KEY_MINUS,
            "_": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_MINUS),
            "=": ecodes.KEY_EQUAL,
            "+": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_EQUAL),
            "/": ecodes.KEY_SLASH,
            "\\": ecodes.KEY_BACKSLASH,
            "[": ecodes.KEY_LEFTBRACE,
            "]": ecodes.KEY_RIGHTBRACE,
            "(": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_9),
            ")": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_0),
        }

        result = []
        for ch in text:
            if ch.isalpha():
                if ch.isupper():
                    result.append(ecodes.KEY_LEFTSHIFT)
                result.append(getattr(ecodes, f"KEY_{ch.upper()}"))
            elif ch.isdigit():
                result.append(getattr(ecodes, f"KEY_{ch}"))
            elif ch in mapping:
                result.append(mapping[ch])
            else:
                print(f"Unsupported character: {repr(ch)}")
        return result

    def __del__(self) -> None:
        for w in self.watchers:
            w.stop()
        print("All keyboard watchers stopped.")
