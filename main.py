from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from noise import snoise2
import os
import random
from Block import *

loadPrcFile('config/general.prc')

if __debug__:
    loadPrcFile('config/dev.prc')

base = ShowBase()

octavesElev = 5
octavesRough = 2
octavesDetail = 1
freq = 16.0 * octavesElev

world = {}

verboseLogging = False
fancyRendering = False
wantNewGeneration = False
fillWorld = False
base.setFrameRateMeter(True)

paused = False

inventory = [DIRT, COBBLESTONE, GLASS, GRASS, BRICKS, WOOD, LEAVES, PLANKS, STONE]
currentBlock = inventory[0]

currentSelectedText = DirectLabel(text="Current block:", text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0), parent=aspect2d,
                                  scale=0.05, pos=(0, 0, -0.9))
currentBlockText = DirectLabel(text=blockNames[currentBlock], text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0),
                               parent=aspect2d, scale=0.05, pos=(0, 0, -0.95))


def pause():
    global paused
    paused = not paused

    if paused:
        base.disableMouse()
        pauseScreen.showPause()
    else:
        base.enableMouse()
        pauseScreen.hide()


class PauseScreen:
    def __init__(self):
        self.pauseScr = aspect2d.attachNewNode(
            "pause")  # This is used so that everything can be stashed at once... except for dim, which is on render2d
        self.loadScr = aspect2d.attachNewNode("load")  # It also helps for flipping between screens
        self.saveScr = aspect2d.attachNewNode("save")

        cm = CardMaker('card')
        self.dim = render2d.attachNewNode(cm.generate())
        self.dim.setPos(-1, 0, -1)
        self.dim.setScale(2)
        self.dim.setTransparency(1)
        self.dim.setColor(0, 0, 0, 0.5)

        self.buttonModel = loader.loadModel('gfx/button')
        inputTexture = loader.loadTexture('gfx/tex/button_press.png')

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
            decButton_geom=(self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
                            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
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
            incButton_geom=(self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
                            self.buttonModel.find('**/button_over'), self.buttonModel.find('**/button_disabled')),
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

        f = []
        if not os.path.exists('saves/'):
            os.makedirs('saves/')
        for (dirpath, dirnames, filenames) in os.walk('saves/'):
            f.extend(filenames)
            break

        for file in f:
            l = DirectButton(geom=(self.buttonModel.find('**/button_up'), self.buttonModel.find('**/button_press'),
                                   self.buttonModel.find('**/button_over'),
                                   self.buttonModel.find('**/button_disabled')),
                             relief=None, scale=0.5, pos=(0, 0, -0.75), text=file.strip('.sav'), text_fg=(1, 1, 1, 1),
                             text_scale=0.1, text_pos=(0, -0.04), command=self.load, extraArgs=[file])
            self.loadList.addItem(l)

    def save(self, worldName=None):
        self.saveText2['text'] = "Saving..."
        if worldName == None:
            worldName = self.saveName.get(True)
        print("Saving %s..." % worldName)
        dest = 'saves/%s.sav' % worldName
        dir = os.path.dirname(dest)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            f = open(dest, 'wt')
        except IOError:
            self.saveText2[
                'text'] = "Could not save. Make sure the world name does not contain the following characters: \\ / : * ? \" < > |"
            print("Failed!")
            return
        for key in world:
            if world[key].type == AIR:
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
            addBlock(AIR, key[0], key[1], key[2])

        world.clear()

        for key in toLoad:
            key = key.split(':')
            posTup = eval(key[0])
            addBlock(int(key[1]), posTup[0], posTup[1], posTup[2])
        f.close()
        self.loadText2['text'] = "Loaded!"
        print("Loaded!")

    def hide(self):
        self.pauseScr.stash()
        self.loadScr.stash()
        self.saveScr.stash()
        self.dim.stash()


pauseScreen = PauseScreen()


def addBlock(blockType, x, y, z):
    try:
        world[(x, y, z)].cleanup()
    except:
        pass
    block = Block(blockType, x, y, z)
    world[(x, y, z)] = block
    return


for x in range(0, 16):
    for y in range(0, 16):
        amplitude = random.randrange(0.0, 5.0)
        blockType = DIRT
        if wantNewGeneration:
            z = max(min(int(snoise2(x / freq, y / freq, octavesElev) + (
            snoise2(x / freq, y / freq, octavesRough) * snoise2(x / freq, y / freq, octavesDetail)) * 64 + 64), 128), 0)
            addBlock(blockType, x, y, z)
        else:
            z = max((int(snoise2(x / freq, y / freq, 5) * amplitude) + 8), 0)
            addBlock(blockType, x, y, z)
        if fillWorld:
            for height in range(0, z + 1):
                addBlock(blockType, x, y, height)
        if verboseLogging:
            print("Generated %s at (%d, %d, %d)" % (blockNames[blockType], x, y, z))

alight = AmbientLight('alight')
alight.setColor(VBase4(0.6, 0.6, 0.6, 1))
alnp = render.attachNewNode(alight)
render.setLight(alnp)
slight = Spotlight('slight')
slight.setColor(VBase4(1, 1, 1, 1))
lens = PerspectiveLens()
slight.setLens(lens)
slnp = render.attachNewNode(slight)
slnp.setPos(8, -9, 128)
slnp.setHpr(0, 270, 0)
render.setLight(slnp)

if fancyRendering:
    # Use a 512x512 resolution shadow map
    slight.setShadowCaster(True, 512, 512)
    # Enable the shader generator for the receiving nodes
    render.setShaderAuto()

traverser = CollisionTraverser()
handler = CollisionHandlerQueue()

pickerNode = CollisionNode('mouseRay')
pickerNP = camera.attachNewNode(pickerNode)
pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
pickerRay = CollisionRay()
pickerNode.addSolid(pickerRay)
traverser.addCollider(pickerNP, handler)


def handlePick(right=False):
    if paused:
        return  # no

    if base.mouseWatcherNode.hasMouse():
        mpos = base.mouseWatcherNode.getMouse()
        pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

        traverser.traverse(render)
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
    global currentBlock
    currentBlock = inventory[slot - 1]
    currentBlockText["text"] = blockNames[currentBlock]
    if verboseLogging:
        print("Selected hotbar slot %d" % slot)
        print("Current block: %s" % blockNames[currentBlock])


base.accept('mouse1', handlePick)
base.accept('mouse3', handlePick, extraArgs=[True])
base.accept('escape', pause)
base.accept('1', hotbarSelect, extraArgs=[1])
base.accept('2', hotbarSelect, extraArgs=[2])
base.accept('3', hotbarSelect, extraArgs=[3])
base.accept('4', hotbarSelect, extraArgs=[4])
base.accept('5', hotbarSelect, extraArgs=[5])
base.accept('6', hotbarSelect, extraArgs=[6])
base.accept('7', hotbarSelect, extraArgs=[7])
base.accept('8', hotbarSelect, extraArgs=[8])
base.accept('9', hotbarSelect, extraArgs=[9])


def handlePickedObject(obj):
    if verboseLogging:
        print("Left clicked a block at %d, %d, %d" % (obj.getX(), obj.getY(), obj.getZ()))
    addBlock(AIR, obj.getX(), obj.getY(), obj.getZ())


def handleRightPickedObject(obj, west, north, east, south, top, bot):
    if verboseLogging:
        print("Right clicked a block at %d, %d, %d, attempting to place %s" % (
        obj.getX(), obj.getY(), obj.getZ(), blockNames[currentBlock]))
    try:
        # not [block face] checks to see if the user clicked on [block face]. this is not confusing at all.
        if world[(obj.getX() - 1, obj.getY(), obj.getZ())].type == AIR and not west:
            addBlock(currentBlock, obj.getX() - 1, obj.getY(), obj.getZ())
        elif world[(obj.getX() + 1, obj.getY(), obj.getZ())].type == AIR and not east:
            addBlock(currentBlock, obj.getX() + 1, obj.getY(), obj.getZ())
        elif world[(obj.getX(), obj.getY() - 1, obj.getZ())].type == AIR and not south:
            addBlock(currentBlock, obj.getX(), obj.getY() - 1, obj.getZ())
        elif world[(obj.getX(), obj.getY() + 1, obj.getZ())].type == AIR and not north:
            addBlock(currentBlock, obj.getX(), obj.getY() + 1, obj.getZ())
        elif world[(obj.getX(), obj.getY(), obj.getZ() + 1)].type == AIR and not top:
            addBlock(currentBlock, obj.getX(), obj.getY(), obj.getZ() + 1)
        elif world[(obj.getX(), obj.getY(), obj.getZ() - 1)].type == AIR and not bot:
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


fog = Fog("fog")
fog.setColor(0.5294, 0.8078, 0.9215)
fog.setExpDensity(0.015)
render.setFog(fog)
base.camLens.setFar(256)

base.run()
