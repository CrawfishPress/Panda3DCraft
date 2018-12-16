"""
Purpose: convert key-presses into a Dictionary of keys being hit

Much of it is way kludgy, because but while Panda3d sends the "shift-arrow_left" single event,
it doesn't send a "shift-arrow_left-up", but two events, "shift" and "arrow_left-up".
Yes, that's "shift", and not even "shift-up". Sigh...

It's likely there are better ways of handling key-presses than this...
"""

# At one point, I had planned to populate this table from the rotate/translate-keys table,
# but decided I prefer it explicitly here, as documentation.
KEYS_HIT = {
    "arrow_left": False,
    "arrow_right": False,
    "arrow_up": False,
    "arrow_down": False,

    "shift-arrow_up": False,
    "shift-arrow_down": False,

    "m": False,  # Toggle Mouse on/off
    "r": False,  # Reset camera
    "q": False,  # Query camera position
    }

TRANSLATE_DATA = {
    "arrow_left": {'dir': (-1, 0, 0), 'axis': 'x', 'scale': 10},
    "arrow_right": {'dir': (1, 0, 0), 'axis': 'x', 'scale': 10},
    "arrow_up": {'dir': (0, 1, 0), 'axis': 'y', 'scale': 20},
    "arrow_down": {'dir': (0, -1, 0), 'axis': 'y', 'scale': 20},

    "shift-arrow_up": {'dir': (0, 0, 1), 'axis': 'z', 'scale': 10},
    "shift-arrow_down": {'dir': (0, 0, -1), 'axis': 'z', 'scale': 10},
    }


def update_key(key, value, keys_hit):

    keys_hit[key] = value
    print("update_key = %s, value = %s" % (key, value))

    if key == 'shift' and not value:
        keys_hit['shift-arrow_up'] = False
        keys_hit['shift-arrow_down'] = False

    if key == 'arrow_up' and not value:
        keys_hit['shift-arrow_up'] = False
    if key == 'arrow_down' and not value:
        keys_hit['shift-arrow_down'] = False
