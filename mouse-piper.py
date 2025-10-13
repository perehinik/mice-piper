#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from typing import Optional
import os
import json

from pynput.keyboard import Listener as KListener, Key, Controller
from pynput.mouse import Listener as MListener, Button


@dataclass
class PiperEvent:
    x: int
    y: int
    button: Button
    pressed: bool

def action_copy(keyboard: Controller, event: PiperEvent) -> None:
    with keyboard.pressed(Key.ctrl):
        keyboard.press('c')
        keyboard.release('c')

def action_paste(keyboard: Controller, event: PiperEvent) -> None:
    with keyboard.pressed(Key.ctrl):
        keyboard.press('v')
        keyboard.release('v')

def action_delete(keyboard: Controller, event: PiperEvent) -> None:
    keyboard.press(Key.delete)
    keyboard.release(Key.delete)

def action_menu(keyboard: Controller, event: PiperEvent) -> None:
    if event.pressed:
        keyboard.press(Key.alt)
        keyboard.press(Key.tab)
        keyboard.release(Key.tab)
    else:
        keyboard.release(Key.alt)

piper_actions = {
    "Copy": action_copy,
    "Paste": action_paste,
    "Menu": action_menu,
    "Delete": action_delete
}

class MousePiper:
    config_dir = "/etc/mouse-piper"
    config_name = "config.json"
    def __init__(self) -> None:
        self.keyboard = Controller()
        self.action_map = {}
        self.read_config()

        self.mouse_button_clicked: Optional[Button] = None

    def on_m_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        button_id = self.get_button_id(button)
        if button_id not in self.action_map:
            return
        action_str = self.action_map[button_id]
        if action_str not in piper_actions:
            return
        action = piper_actions[action_str]
        event = PiperEvent(x=x, y=y, button=button, pressed=pressed)
        action(self.keyboard, event)

    def read_config(self) -> None:
        config_path = os.path.join(self.config_dir, self.config_name)

        if not os.path.exists(config_path):
            print(f"⚠️ Config file not found: {config_path}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Optional: sanity check structure
        if "action_map" in config:
            self.action_map = config["action_map"]

    def save_config(self) -> None:
        config = {"action_map": self.action_map}
        with open(os.path.join(self.config_dir, self.config_name), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def on_m_click_config(self, x: int, y: int, button: Button, pressed: bool) -> bool:
        if pressed:
            self.mouse_button_clicked = button
            return False

    def on_k_press_config(self, key) -> None:
        try:
            if key.char and key.char.upper() == 'X':
                print("❌ Exiting configuration.")
                raise KListener.StopException
            elif key.char and key.char.upper() == 'S':
                print("💾 Saving configuration.")
                self.save_config()
                print("Configuration saved")
                raise KListener.StopException
            elif key.char and key.char.upper() == 'V':
                self.mouse_button_clicked = Button.left
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

    @staticmethod
    def get_button_id(button: Button) -> str:
        return str(button).split(".")[-1]

    def run_listener(self) -> None:
        """
        Start the global mouse listener.
        """
        with MListener(on_click=self.on_m_click) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print(f"\nStopped by user")
                listener.stop()

    def configure(self) -> None:
        while True:
            self.mouse_button_clicked = None
            print("\n👉 Press a mouse button (or 'X' to exit, 'S' to save, 'V' to show config)...")

            # Run mouse listener until a click
            with MListener(on_click=self.on_m_click_config, suppress=True) as m_listener, \
                    KListener(on_press=self.on_k_press_config) as k_listener:
                m_listener.join()

            # If user pressed X or S, we stop keyboard listener too
            if self.mouse_button_clicked is None or self.mouse_button_clicked is Button.left:
                break

            button_id = self.get_button_id(self.mouse_button_clicked)
            print(f"\n🖱 You pressed: {button_id} button.")
            action = self.get_action_config()
            if action:
                self.action_map[button_id] = action
                print(f"✅ Assigned '{action}' to '{button_id}' mouse button")

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
    piper = MousePiper()

    if args.configure:
        piper.configure()
    else:
        piper.run_listener()
