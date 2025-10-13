from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from evdev import ecodes

from piper_device import PiperEvent, PiperKeyboard


@dataclass
class PiperAction:
    name: str
    run: Callable[[PiperKeyboard, PiperEvent], None]
    cleanup: Callable[[PiperKeyboard, Optional[PiperEvent]], None] = None
    data: Dict = field(default_factory=dict)

def action_copy_run(keyboard: PiperKeyboard, event: PiperEvent) -> None:
    keyboard.click_key(ecodes.KEY_C, execute=True)

def action_paste_run(keyboard: PiperKeyboard, event: PiperEvent) -> None:
    keyboard.click_key(ecodes.KEY_V, execute=True)

def action_delete_run(keyboard: PiperKeyboard, event: PiperEvent) -> None:
    keyboard.click_key(ecodes.KEY_DELETE, execute=True)

def action_menu_run(keyboard: PiperKeyboard, event: PiperEvent) -> None:
    if event.pressed:
        keyboard.release_key(ecodes.KEY_LEFTALT, execute=True)
        keyboard.press_key(ecodes.KEY_LEFTALT, execute=False)
        keyboard.click_key(ecodes.KEY_TAB, execute=True)

def action_menu_cleanup(keyboard: PiperKeyboard, event: PiperEvent) -> None:
    if event.pressed or not event:
        keyboard.release_key(ecodes.KEY_LEFTALT, execute=True)

action_list = [
    PiperAction(name="Copy", run=action_copy_run),
    PiperAction(name="Paste", run=action_paste_run),
    PiperAction(name="Menu", run=action_menu_run, cleanup=action_menu_cleanup),
    PiperAction(name="Delete", run=action_delete_run)
]

piper_actions = {action.name: action for action in action_list}
