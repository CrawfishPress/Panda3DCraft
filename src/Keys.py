"""
Purpose: convert key-presses into a Dictionary of keys being hit. It is the
responsibility of other functions to convert keys-hit, to movement.

At one point, I had planned to populate KEYS_HIT from the rotate/translate-keys table,
but decided I prefer it explicitly declared, as documentation.

It's likely there are better ways of handling key-presses than this...
"""

import sys

from src.BlockClass import BLOCKS


KEYS_HIT = {
    "a": False,
    "d": False,
    "w": False,
    "s": False,

    "x": False,
    "z": False,

    "m": False,  # Toggle Mouse on/off
    "r": False,  # Reset camera
    }

TRANSLATE_DATA = {
    "a": {'dir': (-1, 0, 0), 'axis': 'x', 'scale': 10},
    "d": {'dir': (1, 0, 0), 'axis': 'x', 'scale': 10},
    "w": {'dir': (0, 1, 0), 'axis': 'y', 'scale': 20},
    "s": {'dir': (0, -1, 0), 'axis': 'y', 'scale': 20},

    "x": {'dir': (0, 0, 1), 'axis': 'z', 'scale': 10},
    "z": {'dir': (0, 0, -1), 'axis': 'z', 'scale': 10},
    }


def setup_base_keys(the_base, the_keys_hit, call_pause_screen,
                    handle_click, toggle_mouse, reset_stuff, hotbar_select):

    the_base.accept('mouse1', handle_click)
    the_base.accept('mouse3', handle_click, extraArgs=[True])
    the_base.accept('escape', call_pause_screen)

    # Arrow-keys
    for one_key in the_keys_hit.keys():
        the_base.accept(one_key, update_key, [one_key, True, the_keys_hit])
        the_base.accept(one_key + '-up', update_key, [one_key, False, the_keys_hit])

    # Keys that need de-bouncing
    the_base.accept("m", toggle_mouse, ["m", True])
    the_base.accept("m-up", toggle_mouse, ["m", False])
    the_base.accept("r", reset_stuff, ["r", True])
    the_base.accept("r-up", reset_stuff, ["r", False])

    for one_block in BLOCKS.values():
        the_base.accept(str(one_block['hotkey']), hotbar_select, extraArgs=[one_block['hotkey']])


def update_key(key, value, keys_hit):

    keys_hit[key] = value
    # print(f"update_key = {key}, value = {value}")

