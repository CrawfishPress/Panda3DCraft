"""
Purpose: Displays a Menu of available Block types (bitmaps), and lets the user
click on a Block to select that type.

Block bitmaps are stored in Eggs, and have the following structure:
    gfx/btn/{block_type}_{color_type}.png
where 'block_type' = one of the Block key-names ('dirt', etc) and
and color_type = one of the COLORS listed below

And the containing Egg is:
    gfx/{block_type}_btn.egg

To construct the Egg for the 'dirt' block:
    cd gfx
    egg-texture-cards -o dirt_btn.egg -p 240,240 btn/dirt_none.png btn/dirt_yellow.png btn/dirt_green.png

"""

from functools import lru_cache

from src.BlockClass import BLOCKS

# noinspection PyPackageRequirements
from direct.gui.DirectGui import *

# The colors, in order, are: button-up, button-pressed, button-mouseover
# I can't seem to find a way to tell a Button to keep Pressed-state after its released,
# so I just change its button-up color to 'green'.
INACTIVE_COLORS = ('none', 'green', 'yellow')
ACTIVE_COLORS = ('green', 'green', 'yellow')


class BlockMenu(object):
    def __init__(self, base, initial_block='dirt'):
        self.base = base
        self.is_visible = False
        self.blockScr = base.aspect2d.attachNewNode("pause")

        self.loadText = DirectLabel(text="Select Block", parent=self.blockScr,
                                    text_fg=(1, 1, 1, 1),
                                    relief=DGG.GROOVE,
                                    borderWidth=(0.1, 0.1),
                                    frameColor=(1, 0.2, 0, 0.2),
                                    scale=0.075,
                                    pos=(0, 0, 0.55))

        block_names = [btn_key for btn_key in BLOCKS if btn_key != 'air']
        self.buttons = [BlockButton(base, self.blockScr, self.button_clicker, block_name, False)
                        for block_name in block_names]

        for btn in self.buttons:
            if btn.block_type == initial_block:
                btn.activate_me(True)

        self.blockScr.hide()

    def toggle_menu(self):

        if self.is_visible:
            self.blockScr.hide()
        else:
            self.blockScr.show()

        self.is_visible = not self.is_visible

    def button_clicker(self, clicked_button):

        for one_button in self.buttons:
            if one_button == clicked_button:
                clicked_button.activate_me(True)
            else:
                one_button.activate_me(False)

    @property
    def active_block_type(self):

        for one_button in self.buttons:
            if one_button.is_active:
                return one_button.block_type

        return 'air'


class BlockButton(object):
    def __init__(self, base, some_parent, clicker, block_type, active=False):
        self.base = base
        self.parent = some_parent
        self.block_changer = clicker
        self.block_type = block_type
        self.is_active = active

        self.coords = BLOCKS[block_type]['coords']

        some_geom = create_geom(base, block_type, INACTIVE_COLORS)

        self.button = DirectButton(
           geom=some_geom,
           parent=some_parent,
           relief=None,
           pos=self.coords,
           scale=1.0,
           command=self.click_me)

    def click_me(self):

        self.block_changer(self)

    def activate_me(self, activate):

        self.is_active = activate
        if activate:
            next_colors = ACTIVE_COLORS
        else:
            next_colors = INACTIVE_COLORS
        self.button["geom"] = create_geom(self.base, self.block_type, next_colors)
        self.button.resetFrameSize()


@lru_cache()  # Memoization - because we don't want to re-load the same model every time...
def create_geom(base, block_type, color_set):

    button_egg = base.loader.loadModel(f"gfx/{block_type}_btn")
    geom = (button_egg.find(f"**/{block_type}_{color_set[0]}"),
            button_egg.find(f"**/{block_type}_{color_set[1]}"),
            button_egg.find(f"**/{block_type}_{color_set[2]}"))

    return geom
