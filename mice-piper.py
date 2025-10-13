#!/usr/bin/env python3

import argparse
import json
import os
import time
from contextlib import suppress
from typing import Optional, Dict
import subprocess

from evdev import ecodes

from piper_actions import piper_actions, PiperAction
from piper_device import PiperKeyboard, PiperMouse, PiperEvent


class MicePiper:
    config_dir = "/etc/mice-piper"
    config_name = "config.json"
    def __init__(self, config_mode: bool = False) -> None:
        # {<device_name>: {<button_id> : <action>}}
        self.action_map: Dict[str, Dict[str, str]] = {}
        self.config_mode = config_mode
        self.running = True

        self.read_config()

        self.last_key_event: Optional[PiperEvent] = None
        self.last_mouse_event: Optional[PiperEvent] = None
        self.last_action: Optional[PiperAction] = None

        self.mouse = PiperMouse(self.on_m_action)
        self.keyboard = PiperKeyboard(self.on_k_action)

        if self.config_mode:
            self.set_service_state(False)
            self.configure()
            self.set_service_state(True)

    @staticmethod
    def set_service_state(state: bool) -> None:
        with suppress(Exception):
            action = "Start" if state else "Stop"
            service_name = "mice-piper.service"
            print(f"{action} {service_name}")
            subprocess.run(["systemctl", action.lower(), service_name], check=True)

    def on_m_action(self, event: PiperEvent) -> None:
        self.last_mouse_event = event
        if self.last_action and self.last_action.cleanup:
            self.last_action.cleanup(self.keyboard, event)
            self.last_action = None
        if not self.config_mode:
            if event.device.name not in self.action_map:
                return
            button_id = None
            if event.button_id in self.action_map[event.device.name]:
                button_id = event.button_id
            elif str(event.button_id) in self.action_map[event.device.name]:
                button_id = str(event.button_id)
            else:
                return
            action_str = self.action_map[event.device.name][button_id]
            if action_str not in piper_actions:
                return
            action = piper_actions[action_str]
            action.run(self.keyboard, event)
            self.last_action = action

    def on_k_action(self, event: PiperEvent):
        try:
            if self.last_action is not None and self.last_action.cleanup is not None:
                self.last_action.cleanup(self.keyboard, None)
                self.last_action = None
            if self.config_mode and event.pressed:
                self.last_key_event = event
                if event.button_id == ecodes.KEY_X:
                    print("Exiting configuration.")
                    self.running = False
                elif event.button_id == ecodes.KEY_S:
                    self.save_config()
                    print("Configuration saved")
                elif event.button_id == ecodes.KEY_V:
                    for m_key, action in self.action_map.items():
                        print(f"{m_key} : {action}")
        except AttributeError:
            pass

    def read_config(self) -> None:
        config_path = os.path.join(self.config_dir, self.config_name)

        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return

        config = None
        with open(config_path, "r", encoding="utf-8") as f:
            with suppress(Exception):
                config = json.load(f)

        # Optional: sanity check structure
        if config and "action_map" in config:
            self.action_map = config["action_map"]

    def save_config(self) -> None:
        config = {"action_map": self.action_map}
        with open(os.path.join(self.config_dir, self.config_name), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

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
                print("Invalid choice. Try again.")

    def configure(self) -> None:
        while True:
            print("\n👉 Press a mouse button (or 'X' to exit, 'S' to save, 'V' to show config)...")

            self.last_mouse_event = None
            self.last_key_event = None
            # Run mouse listener until a click
            while True:
                time.sleep(0.1)
                if self.last_key_event is not None and self.last_key_event.button_id == ecodes.KEY_X:
                    return
                if self.last_mouse_event:
                    self.last_key_event = None
                    break

            # If user pressed X
            m_event = self.last_mouse_event
            if m_event is None or (self.last_key_event  is not None and self.last_key_event.button_id == ecodes.KEY_X):
                break

            print(f"\nYou pressed: {m_event.button_id}-{m_event.button_name} button.")
            device_name = m_event.device.name
            action = self.get_action_config()
            if action:
                if device_name not in self.action_map:
                    self.action_map[device_name] = {}
                self.action_map[device_name][str(m_event.button_id)] = action
                print(f"Assigned '{action}' to {m_event.button_id}-{m_event.button_name} mouse button")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mice-piper",
        description="Mice Piper — a tool for assigning functions for mouse buttons",
    )

    parser.add_argument(
        "-c", "--configure",
        action="store_true",
        help="Configure mouse buttons."
    )

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    piper = MicePiper(config_mode=args.configure)
    while piper.running:
        time.sleep(1)
