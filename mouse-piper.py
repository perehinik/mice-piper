#!/usr/bin/env python3

import argparse
import json
import os
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Callable
from typing import Optional, List, Dict

from evdev import InputDevice, categorize, ecodes, list_devices, UInput
with suppress(Exception):
    # This is not needed for service
    from pynput.keyboard import Listener as KListener

capabilities = {
    ecodes.EV_KEY: [ecodes.KEY_LEFTALT, ecodes.KEY_TAB, ecodes.KEY_LEFTCTRL, ecodes.BTN_LEFT, ecodes.BTN_RIGHT],
    ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
}

@dataclass
class PiperEvent:
    device: InputDevice
    button_id: str
    button_name: str
    pressed: bool

@dataclass
class PiperAction:
    name: str
    run: Callable[[UInput, PiperEvent], None]
    cleanup: Callable[[UInput, Optional[PiperEvent]], None] = None
    data: Dict = field(default_factory=dict)

def action_copy_run(keyboard: UInput, event: PiperEvent) -> None:
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_C, 1)
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_C, 0)
    keyboard.syn()

def action_paste_run(keyboard: UInput, event: PiperEvent) -> None:
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
    keyboard.syn()

def action_delete_run(keyboard: UInput, event: PiperEvent) -> None:
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_DELETE, 1)
    keyboard.write(ecodes.EV_KEY, ecodes.KEY_DELETE, 0)
    keyboard.syn()

def action_menu_run(keyboard: UInput, event: PiperEvent) -> None:
    if event.pressed:
        keyboard.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0)
        keyboard.syn()
        keyboard.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1)  # Alt down
        keyboard.write(ecodes.EV_KEY, ecodes.KEY_TAB, 1)  # Tab down
        keyboard.write(ecodes.EV_KEY, ecodes.KEY_TAB, 0)  # Tab up
        keyboard.syn()

def action_menu_cleanup(keyboard: UInput, event: PiperEvent) -> None:
    if event.pressed or not event:
        keyboard.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0)  # Tab up
        keyboard.syn()

action_list = [
    PiperAction(name="Copy", run=action_copy_run),
    PiperAction(name="Paste", run=action_paste_run),
    PiperAction(name="Menu", run=action_menu_run, cleanup=action_menu_cleanup),
    PiperAction(name="Delete", run=action_delete_run)
]

piper_actions = {action.name: action for action in action_list}

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
                        button_id=str(event.code),
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

class MousePiper:
    config_dir = "/etc/mouse-piper"
    config_name = "config.json"
    def __init__(self, config_mode: bool = False) -> None:
        # {<device_name>: {<button_id> : <action>}}
        self.action_map: Dict[str, Dict[str, str]] = {}
        self.config_mode = config_mode
        self.running = True

        self.watchers: List[DeviceWatcher] = []
        self.devices: List[InputDevice] = []

        self.read_config()
        self.initialise_devices()

        self.keyboard = UInput(capabilities, name="virtual-mouse-kb")
        self.last_key_pressed: Optional[str] = None
        self.last_mouse_event: Optional[PiperEvent] = None
        self.last_action: Optional[PiperAction] = None

        if self.config_mode:
            self.k_listener = KListener(on_press=self.on_k_press)
            self.k_listener.start()
            self.configure()

    def on_m_click(self, event: PiperEvent) -> None:
        self.last_mouse_event = event
        if self.last_action and self.last_action.cleanup:
            self.last_action.cleanup(self.keyboard, event)
            self.last_action = None
        if not self.config_mode:
            if event.device.name not in self.action_map:
                return
            if event.button_id not in self.action_map[event.device.name]:
                return
            action_str = self.action_map[event.device.name][event.button_id]
            if action_str not in piper_actions:
                return
            action = piper_actions[action_str]
            action.run(self.keyboard, event)
            self.last_action = action

    def read_config(self) -> None:
        config_path = os.path.join(self.config_dir, self.config_name)

        if not os.path.exists(config_path):
            print(f"⚠️ Config file not found: {config_path}")
            return

        config = None
        with open(config_path, "r", encoding="utf-8") as f:
            with suppress(Exception):
                config = json.load(f)

        # Optional: sanity check structure
        if config and "action_map" in config:
            self.action_map = config["action_map"]

    def initialise_devices(self) -> None:
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
                watcher = DeviceWatcher(dev, self.on_m_click)
                self.watchers.append(watcher)
                watcher.start()

    def save_config(self) -> None:
        config = {"action_map": self.action_map}
        with open(os.path.join(self.config_dir, self.config_name), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def on_k_press(self, key):
        try:
            if self.last_action is not None and self.last_action.cleanup is not None:
                self.last_action.cleanup(self.keyboard, None)
                self.last_action = None
            if self.config_mode:
                self.last_key_pressed = key.char.upper()
                if key.char and key.char.upper() == 'X':
                    print("❌ Exiting configuration.")
                    self.running = False
                elif key.char and key.char.upper() == 'S':
                    print("💾 Saving configuration.")
                    self.save_config()
                    print("Configuration saved")
                elif key.char and key.char.upper() == 'V':
                    for m_key, action in self.action_map.items():
                        print(f"{m_key} : {action}")
        except AttributeError:
            pass

    @staticmethod
    def get_action_config() -> Optional[str]:
        print("Select action:")
        for idx, act in enumerate(piper_actions.keys(), start=1):
            print(f"  {idx}. {act}")

        # Get user choice
        while True:
            choice = input("Enter action number (or 'C' to cancel): ").strip().upper()
            if choice == 'C':
                print("Canceled.")
                return
            elif choice.isdigit() and 1 <= int(choice) <= len(piper_actions.keys()):
                return list(piper_actions.keys())[int(choice) - 1]
            else:
                print("⚠️ Invalid choice. Try again.")

    def configure(self) -> None:
        while True:
            print("\n👉 Press a mouse button (or 'X' to exit, 'S' to save, 'V' to show config)...")

            self.last_mouse_event = None
            self.last_key_pressed = None
            # Run mouse listener until a click
            while True:
                time.sleep(0.1)
                if self.last_key_pressed == "X":
                    return
                if self.last_mouse_event:
                    break

            # If user pressed X or S, we stop keyboard listener too
            if self.last_mouse_event is None or self.last_key_pressed:
                break

            print(f"\n🖱 You pressed: {self.last_mouse_event.button_name} button.")
            device_name = self.last_mouse_event.device.name
            action = self.get_action_config()
            if action:
                if device_name not in self.action_map:
                    self.action_map[device_name] = {}
                self.action_map[device_name][self.last_mouse_event.button_id] = action
                print(f"✅ Assigned '{action}' to '{self.last_mouse_event.button_id}' mouse button")

    def __del__(self):
        for w in self.watchers:
            w.stop()
        self.k_listener.stop()
        print("All watchers stopped.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mouse-piper",
        description="Mouse Piper — a tool for assigning functions for mouse buttons",
    )

    parser.add_argument(
        "-c", "--configure",
        action="store_true",
        help="Configure mouse buttons."
    )

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    piper = MousePiper(config_mode=args.configure)
    while piper.running:
        time.sleep(1)
