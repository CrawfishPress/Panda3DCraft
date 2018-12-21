from functools import lru_cache

from src.BlockClass import BLOCKS

# noinspection PyPackageRequirements
from direct.gui.DirectGui import *

INACTIVE_COLORS = ('none', 'green', 'yellow')
ACTIVE_COLORS = ('green', 'green', 'yellow')


class BlockMenu(object):
    def __init__(self, base):
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

        self.buttons = [BlockButton(base, self.blockScr, self.button_clicker, 'dirt', False),
                        BlockButton(base, self.blockScr, self.button_clicker, 'bricks', False),
                        BlockButton(base, self.blockScr, self.button_clicker, 'cobblestone', False),
                        ]

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
                clicked_button.activate_me(True, ACTIVE_COLORS)
            else:
                one_button.activate_me(False, INACTIVE_COLORS)

    @property
    def active_block_type(self):

        for one_button in self.buttons:
            if one_button.active:
                return one_button.block_type

        return 'air'


class BlockButton(object):
    def __init__(self, base, some_parent, clicker, block_type='air', active=False):
        self.base = base
        self.parent = some_parent
        self.block_changer = clicker
        self.block_type = block_type
        self.active = active

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

    def activate_me(self, activate, active_colors):

        self.active = activate
        some_geom = create_geom(self.base, self.block_type, active_colors)

        self.button["geom"] = some_geom
        self.button.resetFrameSize()


@lru_cache()  # Memoization - because we don't want to re-load the same model every time...
def create_geom(base, block_type, color_set):

    button_egg = base.loader.loadModel(f"gfx/{block_type}_btn")
    geom = (button_egg.find(f"**/{block_type}_{color_set[0]}"),
            button_egg.find(f"**/{block_type}_{color_set[1]}"),
            button_egg.find(f"**/{block_type}_{color_set[2]}"))

    return geom
