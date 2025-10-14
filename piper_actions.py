from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from evdev import ecodes

from piper_device import PiperEvent, PiperKeyboard


@dataclass
class PiperAction:
    name: str
    run: Callable[[PiperKeyboard, PiperEvent, Optional[Dict]], None] = None
    cleanup: Callable[[PiperKeyboard, Optional[PiperEvent], Optional[Dict]], None] = None
    data: Dict = field(default_factory=dict)

def action_copy_run(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_C)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_paste_run(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_V)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_select_all(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_A)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_new_tab(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_T)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_close_tab(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_W)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_save(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.click_key(ecodes.KEY_S)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_delete_run(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.click_key(ecodes.KEY_DELETE, execute=True)

def action_menu_run(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.release_key(ecodes.KEY_LEFTALT, execute=True)
        keyboard.press_key(ecodes.KEY_LEFTALT, execute=False)
        keyboard.click_key(ecodes.KEY_TAB, execute=True)

def action_menu_cleanup(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed or not event:
        keyboard.release_key(ecodes.KEY_LEFTALT, execute=True)

def action_menu_close_current_window(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTALT)
        keyboard.click_key(ecodes.KEY_F4)
        keyboard.release_key(ecodes.KEY_LEFTALT, execute=True)

def action_minimise_all(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTMETA)
        keyboard.click_key(ecodes.KEY_D)
        keyboard.release_key(ecodes.KEY_LEFTMETA, execute=True)

def action_new_terminal(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed:
        keyboard.press_key(ecodes.KEY_LEFTCTRL)
        keyboard.press_key(ecodes.KEY_LEFTALT)
        keyboard.click_key(ecodes.KEY_T)
        keyboard.release_key(ecodes.KEY_LEFTALT)
        keyboard.release_key(ecodes.KEY_LEFTCTRL, execute=True)

def action_type_custom_text(keyboard: PiperKeyboard, event: PiperEvent, data: Dict = None) -> None:
    if event.pressed and data and "text" in data:
        keyboard.type_string(str(data["text"]))

action_list = [
    PiperAction(name="Copy", run=action_copy_run),
    PiperAction(name="Paste", run=action_paste_run),
    PiperAction(name="Select all", run=action_select_all),
    PiperAction(name="Save", run=action_save),
    PiperAction(name="Delete", run=action_delete_run),
    PiperAction(name="Type Custom Text", run=action_type_custom_text),
    PiperAction(name="Menu", run=action_menu_run, cleanup=action_menu_cleanup),
    PiperAction(name="Close current window", run=action_menu_close_current_window),
    PiperAction(name="Minimise all windows", run=action_minimise_all),
    PiperAction(name="New terminal", run=action_new_terminal),
]

piper_actions = {action.name: action for action in action_list}
