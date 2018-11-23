from contextlib import suppress
from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from noise import snoise2
import os
import random
from Block import *

Core.loadPrcFile('config/general.prc')

if __debug__:  # True unless Python is started with -O
    print("debug-mode on")
    Core.loadPrcFile('config/dev.prc')

octavesElev = 5
octavesRough = 2
octavesDetail = 1
freq = 16.0 * octavesElev

verboseLogging = True
fancyRendering = False
wantNewGeneration = False
fillWorld = False

paused = False
pickerRay = None
traverser = None
handler = None
pause_menu = None

world = {}

currentBlock = 'dirt'
currentBlockText = None

base = ShowBase()


def pause():
    global paused, pause_menu
    paused = not paused

    if not pause_menu:
        pause_menu = PauseScreen()

    if paused:
        base.disableMouse()
        pause_menu.showPause()
    else:
        base.enableMouse()
        pause_menu.hide()


class PauseScreen:
    def __init__(self):
        # This is used so that everything can be stashed at once... except for dim, which is on render2d
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
                             relief=None, scale=0.5, pos=(0, 0, -0.75), text=one_file.strip('.sav'), text_fg=(1, 1, 1, 1),
                             text_scale=0.1, text_pos=(0, -0.04), command=self.load, extraArgs=[one_file])
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
        for key in world:
            if world[key].type == 'air':
                continue
            f.write(str(key) + ':')
            f.write(str(world[key].type) + '\n')
        f.close()
        self.saveText2['text'] = "Saved!"
        print("Saved!")

    def load(self, worldName):
        self.loadText2['text'] = "Loading..."
        print("Loading...")
        f = open('saves/%s' % worldName, 'r')
        toLoad = f.read().split('\n')
        toLoad.pop()  # get rid of newline

        for key in world:
            addBlock('air', key[0], key[1], key[2])

        world.clear()

        for key in toLoad:
            key = key.split(':')
            posTup = eval(key[0])
#            addBlock(int(key[1]), posTup[0], posTup[1], posTup[2])
            addBlock('stone', posTup[0], posTup[1], posTup[2])
        f.close()
        self.loadText2['text'] = "Loaded!"
        print("Loaded!")

    def hide(self):
        self.pauseScr.stash()
        self.loadScr.stash()
        self.saveScr.stash()
        self.dim.stash()


def addBlock(blockType, x, y, z):
    global base, world

    with suppress(KeyError, AttributeError):
        world[(x, y, z)].cleanup()

    block = Block(blockType, base, x, y, z)
    world[(x, y, z)] = block


def build_world():

    global pickerRay, traverser, handler, base

    for x in range(0, 16):
        for y in range(0, 16):
            amplitude = random.randrange(0.0, 5.0)
            blockType = 'dirt'
            if wantNewGeneration:
                z = max(min(int(snoise2(x / freq, y / freq, octavesElev) + (
                    snoise2(x / freq, y / freq, octavesRough) *
                        snoise2(x / freq, y / freq, octavesDetail)) * 64 + 64), 128), 0)
                addBlock(blockType, x, y, z)
            else:
                z = max((int(snoise2(x / freq, y / freq, 5) * amplitude) + 8), 0)
                addBlock(blockType, x, y, z)
            if fillWorld:
                for height in range(0, z + 1):
                    addBlock(blockType, x, y, height)
            if verboseLogging:
                print("Generated %s at (%d, %d, %d)" % (blockType, x, y, z))

    alight = Core.AmbientLight('alight')
    alight.setColor(Core.VBase4(0.6, 0.6, 0.6, 1))
    alnp = base.render.attachNewNode(alight)
    base.render.setLight(alnp)
    slight = Core.Spotlight('slight')
    slight.setColor(Core.VBase4(1, 1, 1, 1))
    lens = Core.PerspectiveLens()
    slight.setLens(lens)
    slnp = base.render.attachNewNode(slight)
    slnp.setPos(8, -9, 128)
    slnp.setHpr(0, 270, 0)
    base.render.setLight(slnp)

    if fancyRendering:
        # Use a 512x512 resolution shadow map
        slight.setShadowCaster(True, 512, 512)
        # Enable the shader generator for the receiving nodes
        base.render.setShaderAuto()

    traverser = Core.CollisionTraverser()
    handler = Core.CollisionHandlerQueue()

    pickerNode = Core.CollisionNode('mouseRay')
    pickerNP = base.camera.attachNewNode(pickerNode)
    pickerNode.setFromCollideMask(Core.GeomNode.getDefaultCollideMask())
    pickerRay = Core.CollisionRay()
    pickerNode.addSolid(pickerRay)
    traverser.addCollider(pickerNP, handler)


def handlePick(right=False):

    global pickerRay, traverser, handler, paused

    if paused:
        return

    if base.mouseWatcherNode.hasMouse():
        mpos = base.mouseWatcherNode.getMouse()
        pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

        traverser.traverse(base.render)
        if handler.getNumEntries() > 0:
            handler.sortEntries()
            pickedObj = handler.getEntry(0).getIntoNodePath()
            pickedObj = pickedObj.findNetTag('blockTag')
            if not pickedObj.isEmpty():
                if right:
                    handleRightPickedObject(pickedObj,
                                            handler.getEntry(0).getIntoNodePath().findNetTag('westTag').isEmpty(),
                                            handler.getEntry(0).getIntoNodePath().findNetTag('northTag').isEmpty(),
                                            handler.getEntry(0).getIntoNodePath().findNetTag('eastTag').isEmpty(),
                                            handler.getEntry(0).getIntoNodePath().findNetTag('southTag').isEmpty(),
                                            handler.getEntry(0).getIntoNodePath().findNetTag('topTag').isEmpty(),
                                            handler.getEntry(0).getIntoNodePath().findNetTag('botTag').isEmpty())
                else:
                    handlePickedObject(pickedObj)


def hotbarSelect(slot):

    global currentBlock, currentBlockText

    next_block_name = [block_name for block_name, block_val in BLOCKS.items() if block_val['hotkey'] == slot][0]
    currentBlock = next_block_name
    currentBlockText["text"] = next_block_name

    if verboseLogging:
        print("Selected hotbar slot %d" % slot)
        print("Current block: %s" % next_block_name)


def setup_base_keys():
    global base

    base.accept('mouse1', handlePick)
    base.accept('mouse3', handlePick, extraArgs=[True])
    base.accept('escape', pause)

    for one_block in BLOCKS.values():
        base.accept(str(one_block['hotkey']), hotbarSelect, extraArgs=[one_block['hotkey']])


def handlePickedObject(obj):
    if verboseLogging:
        print("Left clicked a block at [%d, %d, %d]" % (obj.getX(), obj.getY(), obj.getZ()))

    addBlock('air', obj.getX(), obj.getY(), obj.getZ())


def handleRightPickedObject(obj, west, north, east, south, top, bot):
    if verboseLogging:
        print("Right clicked a block at [ %d, %d, %d], attempting to place [%s]" % (
            obj.getX(), obj.getY(), obj.getZ(), currentBlock))
    try:
        # not [block face] checks to see if the user clicked on [block face]. this is not confusing at all.
        if world[(obj.getX() - 1, obj.getY(), obj.getZ())].type == 'air' and not west:
            addBlock(currentBlock, obj.getX() - 1, obj.getY(), obj.getZ())
        elif world[(obj.getX() + 1, obj.getY(), obj.getZ())].type == 'air' and not east:
            addBlock(currentBlock, obj.getX() + 1, obj.getY(), obj.getZ())
        elif world[(obj.getX(), obj.getY() - 1, obj.getZ())].type == 'air' and not south:
            addBlock(currentBlock, obj.getX(), obj.getY() - 1, obj.getZ())
        elif world[(obj.getX(), obj.getY() + 1, obj.getZ())].type == 'air' and not north:
            addBlock(currentBlock, obj.getX(), obj.getY() + 1, obj.getZ())
        elif world[(obj.getX(), obj.getY(), obj.getZ() + 1)].type == 'air' and not top:
            addBlock(currentBlock, obj.getX(), obj.getY(), obj.getZ() + 1)
        elif world[(obj.getX(), obj.getY(), obj.getZ() - 1)].type == 'air' and not bot:
            addBlock(currentBlock, obj.getX(), obj.getY(), obj.getZ() - 1)
    except KeyError:
        if not west:
            addBlock(currentBlock, obj.getX() - 1, obj.getY(), obj.getZ())
        elif not east:
            addBlock(currentBlock, obj.getX() + 1, obj.getY(), obj.getZ())
        elif not south:
            addBlock(currentBlock, obj.getX(), obj.getY() - 1, obj.getZ())
        elif not north:
            addBlock(currentBlock, obj.getX(), obj.getY() + 1, obj.getZ())
        elif not top:
            addBlock(currentBlock, obj.getX(), obj.getY(), obj.getZ() + 1)
        elif not bot:
            addBlock(currentBlock, obj.getX(), obj.getY(), obj.getZ() - 1)


def setup_fog():

    global currentBlockText, base

    fog = Core.Fog("fog")
    fog.setColor(0.5294, 0.8078, 0.9215)
    fog.setExpDensity(0.015)
    base.render.setFog(fog)
    base.camLens.setFar(256)

    base.setFrameRateMeter(True)

    currentBlockText = DirectLabel(text=currentBlock, text_fg=(1, 1, 1, 1),
                                   frameColor=(0, 0, 0, 0),
                                   parent=base.aspect2d, scale=0.05, pos=(0, 0, -0.95))


def run_the_world():
    print("working")

    build_world()
    setup_base_keys()
    setup_fog()
    base.run()


if __name__ == '__main__':
    run_the_world()
