"""
Purpose: do lots of stuff - show a Pause-menu, with several options.
Note that this was broken before, when I changed Camera-movement
(which required Mouse-behavior changes). The fix was to re-enable
the Mouse before showing this screen.

Note that I don't re-disable the Mouse afterwards, because it would
require yet another Global variable to keep track of. Just means that
the player has to hit 'm' again to return to Camera-movement mode. Wups...
"""

import os

from panda3d.core import *
import panda3d.core as core
# noinspection PyPackageRequirements
from direct.gui.DirectGui import *

from src.World import add_block as add_block_func


class PauseScreen:
    def __init__(self, base, world, scale=1.0):
        self.is_paused = False
        self.base = base
        self.world = world
        self.scale = scale
        self.addBlock_func = add_block_func
        self.pauseScr = base.aspect2d.attachNewNode("pause")
        self.loadScr = base.aspect2d.attachNewNode("load")  # It also helps for flipping between screens
        self.saveScr = base.aspect2d.attachNewNode("save")

        cm = core.CardMaker('card')
        self.dim = base.render2d.attachNewNode(cm.generate())
        self.dim.setPos(-1, 0, -1)
        self.dim.setScale(2)
        self.dim.setTransparency(1)
        self.dim.setColor(0, 0, 0, 0.5)

        self.buttonModel = base.loader.loadModel('gfx/button')
        input_texture = base.loader.loadTexture('gfx/tex/button_press.png')

        # Pause Screen
        self.unpauseButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, 0.3),
                                  text="Resume Game", text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                  command=self.pause)
        self.saveButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, 0.15), text="Save Game",
                                  text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04), command=self.show_save)
        self.loadButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, -0.15),
                                  text="Load Game", text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                  command=self.show_load)
        self.exitButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, -0.3), text="Quit Game",
                                  text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04), command=exit)

        # Save Screen
        self.saveText = DirectLabel(text="Type in a name for your world", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0),
                                    parent=self.saveScr, scale=0.075, pos=(0, 0, 0.35))
        self.saveText2 = DirectLabel(text="", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0), parent=self.saveScr,
                                     scale=0.06, pos=(0, 0, -0.45))
        self.saveName = DirectEntry(text="", scale=.15, command=self.save, initialText="My World", numLines=1, focus=1,
                                    frameTexture=input_texture, parent=self.saveScr, text_fg=(1, 1, 1, 1),
                                    pos=(-0.6, 0, 0.1), text_scale=0.75)
        self.saveGameBtn = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.saveScr, scale=0.5, pos=(0, 0, -0.1), text="Save",
                                  text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04), command=self.save)
        self.backButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.saveScr, scale=0.5, pos=(0, 0, -0.25), text="Back",
                                  text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                  command=self.show_pause)

        # Load Screen
        num_items_visible = 3
        item_height = 0.15

        self.loadList = DirectScrolledList(
            decButton_pos=(0.35, 0, 0.5),
            decButton_text="^",
            decButton_text_scale=0.04,
            decButton_text_pos=(0, -0.025),
            decButton_text_fg=(1, 1, 1, 1),
            decButton_borderWidth=(0.005, 0.005),
            decButton_scale=(1.5, 1, 2),
            decButton_geom=(self.buttonModel.find('**/button_up'),
                            self.buttonModel.find('**/button_press'),
                            self.buttonModel.find('**/button_over'),
                            self.buttonModel.find('**/button_disabled')),
            decButton_geom_scale=0.1,
            decButton_relief=None,

            incButton_pos=(0.35, 0, 0),
            incButton_text="^",
            incButton_text_scale=0.04,
            incButton_text_pos=(0, -0.025),
            incButton_text_fg=(1, 1, 1, 1),
            incButton_borderWidth=(0.005, 0.005),
            incButton_hpr=(0, 180, 0),
            incButton_scale=(1.5, 1, 2),
            incButton_geom=(self.buttonModel.find('**/button_up'),
                            self.buttonModel.find('**/button_press'),
                            self.buttonModel.find('**/button_over'),
                            self.buttonModel.find('**/button_disabled')),
            incButton_geom_scale=0.1,
            incButton_relief=None,

            frameSize=(-0.4, 1.1, -0.1, 0.59),
            frameTexture=input_texture,
            frameColor=(1, 1, 1, 0.75),
            pos=(-0.45, 0, -0.25),
            scale=1.25,
            numItemsVisible=num_items_visible,
            forceHeight=item_height,
            itemFrame_frameSize=(-0.2, 0.2, -0.37, 0.11),
            itemFrame_pos=(0.35, 0, 0.4),
            itemFrame_frameColor=(0, 0, 0, 0),
            parent=self.loadScr
        )
        self.backButton = DirectButton(geom=(
           self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
           self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                 relief=None, parent=self.loadScr, scale=0.5, pos=(0, 0, -0.5), text="Back",
                                 text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                 command=self.show_pause)
        self.loadText = DirectLabel(text="Select World", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0),
                                    parent=self.loadScr, scale=0.075, pos=(0, 0, 0.55))
        self.loadText2 = DirectLabel(text="", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0), parent=self.loadScr,
                                     scale=0.075, pos=(0, 0, -0.7))

        self.hide()

    def show_pause(self):

        self.saveScr.stash()
        self.loadScr.stash()
        self.pauseScr.unstash()
        self.dim.unstash()

    def show_save(self):

        self.pauseScr.stash()
        self.saveScr.unstash()
        self.saveText2['text'] = ""

    def show_load(self):

        self.pauseScr.stash()
        self.loadScr.unstash()
        self.loadText2['text'] = ""

        self.loadList.removeAndDestroyAllItems()

        file_list = []
        if not os.path.exists('saves/'):
            os.makedirs('saves/')
        for (dirpath, dirnames, filenames) in os.walk('saves/'):
            file_list.extend(filenames)
            break

        for one_file in file_list:
            l = DirectButton(geom=(self.buttonModel.find('**/button_up'),
                                   self.buttonModel.find('**/button_press'),
                                   self.buttonModel.find('**/button_over'),
                                   self.buttonModel.find('**/button_disabled')),
                             relief=None, scale=0.5, pos=(0, 0, -0.75),
                             text=one_file.strip('.sav'), text_fg=(1, 1, 1, 1),
                             text_scale=0.1, text_pos=(0, -0.04), command=self.load,
                             extraArgs=[one_file])
            self.loadList.addItem(l)

    def save(self, world_name=None):

        self.saveText2['text'] = "Saving..."
        if not world_name:
            world_name = self.saveName.get(True)
        print(f"Saving [{world_name}]...")
        dest = f"saves/{world_name}.sav"
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        try:
            f = open(dest, 'wt')
        except IOError:
            self.saveText2[
                'text'] = "Could not save. Make sure the world name " \
                          "does not contain the following characters: \\ / : * ? \" < > |"
            print("Failed!")
            return
        for key in self.world:
            if self.world[key].type == 'air':
                continue
            f.write(str(key) + ':')
            f.write(str(self.world[key].type) + '\n')
        f.close()
        self.saveText2['text'] = "Saved!"
        print("Saved!")

    def load(self, world_name):
        self.loadText2['text'] = "Loading..."
        print("Loading...")
        f = open(f"saves/{world_name}", 'r')
        to_load = f.read().split('\n')
        to_load.pop()  # get rid of newline

        for key in self.world:
            self.addBlock_func('air', key[0], key[1], key[2], self.world, self.base, self.scale)

        self.world.clear()

        for key in to_load:
            key = key.split(':')
            pos_tup = eval(key[0])
            self.addBlock_func(key[1], pos_tup[0], pos_tup[1], pos_tup[2], self.world, self.base, self.scale)
        f.close()
        self.loadText2['text'] = "Loaded!"
        print("Loaded!")

    def hide(self):

        self.pauseScr.stash()
        self.loadScr.stash()
        self.saveScr.stash()
        self.dim.stash()

    def pause(self):

        self.is_paused = not self.is_paused

        if self.is_paused:
            self.show_pause()
        else:
            self.hide()
