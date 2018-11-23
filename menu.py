from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
import os

PAUSE_MENU = None


def setup_pause_menu(base, world, addBlock):
    global PAUSE_MENU

    PAUSE_MENU = PauseScreen(base, world, addBlock)


def is_paused():
    global PAUSE_MENU

    return PAUSE_MENU.is_paused


def pause():
    global PAUSE_MENU

    PAUSE_MENU.is_paused = not PAUSE_MENU.is_paused

    if PAUSE_MENU.is_paused:
        PAUSE_MENU.base.disableMouse()
        PAUSE_MENU.showPause()
    else:
        PAUSE_MENU.base.enableMouse()
        PAUSE_MENU.hide()


class PauseScreen:
    def __init__(self, base, world, addBlock_func):
        self.is_paused = False
        self.base = base
        self.world = world
        self.addBlock_func = addBlock_func
        self.pauseScr = base.aspect2d.attachNewNode("pause")
        self.loadScr = base.aspect2d.attachNewNode("load")  # It also helps for flipping between screens
        self.saveScr = base.aspect2d.attachNewNode("save")

        cm = Core.CardMaker('card')
        self.dim = base.render2d.attachNewNode(cm.generate())
        self.dim.setPos(-1, 0, -1)
        self.dim.setScale(2)
        self.dim.setTransparency(1)
        self.dim.setColor(0, 0, 0, 0.5)

        self.buttonModel = base.loader.loadModel('gfx/button')
        inputTexture = base.loader.loadTexture('gfx/tex/button_press.png')

        # Pause Screen
        self.unpauseButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, 0.3),
                                  text="Resume Game", text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                  command=pause)
        self.saveButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, 0.15), text="Save Game",
                                  text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04), command=self.showSave)
        self.loadButton = DirectButton(geom=(
            self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
                                  relief=None, parent=self.pauseScr, scale=0.5, pos=(0, 0, -0.15),
                                  text="Load Game", text_fg=(1, 1, 1, 1), text_scale=0.1, text_pos=(0, -0.04),
                                  command=self.showLoad)
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
                                    frameTexture=inputTexture, parent=self.saveScr, text_fg=(1, 1, 1, 1),
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
                                  command=self.showPause)

        # Load Screen
        numItemsVisible = 3
        itemHeight = 0.15

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
            frameTexture=inputTexture,
            frameColor=(1, 1, 1, 0.75),
            pos=(-0.45, 0, -0.25),
            scale=1.25,
            numItemsVisible=numItemsVisible,
            forceHeight=itemHeight,
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
                                 command=self.showPause)
        self.loadText = DirectLabel(text="Select World", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0),
                                    parent=self.loadScr, scale=0.075, pos=(0, 0, 0.55))
        self.loadText2 = DirectLabel(text="", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0), parent=self.loadScr,
                                     scale=0.075, pos=(0, 0, -0.7))

        self.hide()

    def showPause(self):
        self.saveScr.stash()
        self.loadScr.stash()
        self.pauseScr.unstash()
        self.dim.unstash()

    def showSave(self):
        self.pauseScr.stash()
        self.saveScr.unstash()
        self.saveText2['text'] = ""

    def showLoad(self):
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

    def save(self, worldName=None):

        self.saveText2['text'] = "Saving..."
        if not worldName:
            worldName = self.saveName.get(True)
        print("Saving %s..." % worldName)
        dest = 'saves/%s.sav' % worldName
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

    def load(self, worldName):
        self.loadText2['text'] = "Loading..."
        print("Loading...")
        f = open('saves/%s' % worldName, 'r')
        toLoad = f.read().split('\n')
        toLoad.pop()  # get rid of newline

        for key in self.world:
            self.addBlock_func('air', key[0], key[1], key[2])

        self.world.clear()

        for key in toLoad:
            key = key.split(':')
            posTup = eval(key[0])
            # TODO: fix this, just a kludge to get rest of game working
#            addBlock(int(key[1]), posTup[0], posTup[1], posTup[2])
            self.addBlock_func('stone', posTup[0], posTup[1], posTup[2])
        f.close()
        self.loadText2['text'] = "Loaded!"
        print("Loaded!")

    def hide(self):
        self.pauseScr.stash()
        self.loadScr.stash()
        self.saveScr.stash()
        self.dim.stash()


