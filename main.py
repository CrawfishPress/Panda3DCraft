from contextlib import suppress
import random

from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from noise import snoise2

from Block import *
from menu import setup_pause_menu, is_paused, pause

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

pickerRay = None
traverser = None
handler = None
PAUSE_MENU = None

currentBlock = 'dirt'
currentBlockText = None

world = {}
base = ShowBase()


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


def handlePick(right_click=False):

    global pickerRay, traverser, handler, base, world

    if is_paused():
        return

    if not base.mouseWatcherNode.hasMouse():
        return

    mpos = base.mouseWatcherNode.getMouse()
    pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

    traverser.traverse(base.render)
    if handler.getNumEntries() <= 0:
        return

    handler.sortEntries()
    pickedObj = handler.getEntry(0).getIntoNodePath()
    pickedObj = pickedObj.findNetTag('blockTag')
    if pickedObj.isEmpty():
        return

    if right_click:
        addBlockObject(pickedObj, handler.getEntry(0).getIntoNodePath())
    else:
        removeBlockObject(pickedObj)


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


def removeBlockObject(obj):

    if verboseLogging:
        print("Left clicked a block at [%d, %d, %d]" % (obj.getX(), obj.getY(), obj.getZ()))

    # We have to add the Block in order to destroy it...
    addBlock('air', obj.getX(), obj.getY(), obj.getZ())


def addBlockObject(obj, node_path):

    if verboseLogging:
        print("Right clicked a block at [%d, %d, %d], attempting to place [%s]" % (
            obj.getX(), obj.getY(), obj.getZ(), currentBlock))

    moves = {
        'west': {'delta_x': -1, 'delta_y': 0, 'delta_z': 0,
                 'clicked': not node_path.findNetTag('westTag').isEmpty()},
        'east': {'delta_x': 1, 'delta_y': 0, 'delta_z': 0,
                 'clicked': not node_path.findNetTag('eastTag').isEmpty()},
        'south': {'delta_x': 0, 'delta_y': -1, 'delta_z': 0,
                  'clicked': not node_path.findNetTag('southTag').isEmpty()},
        'north': {'delta_x': 0, 'delta_y': 1, 'delta_z': 0,
                  'clicked': not node_path.findNetTag('northTag').isEmpty()},
        'top': {'delta_x': 0, 'delta_y': 0, 'delta_z': 1,
                'clicked': not node_path.findNetTag('topTag').isEmpty()},
        'bot': {'delta_x': 0, 'delta_y': 0, 'delta_z': -1,
                'clicked': not node_path.findNetTag('botTag').isEmpty()},
        }

    blocks_clicked = [one_block for one_block in moves.values() if one_block['clicked']]
    if __debug__:
        assert len(blocks_clicked) == 1
    new_block = blocks_clicked[0]

    # Find coords of "new" block
    obj_x, obj_y, obj_z = obj.getX(), obj.getY(), obj.getZ()
    delta_x, delta_y, delta_z = new_block['delta_x'], new_block['delta_y'], new_block['delta_z']
    new_coords = (obj_x + delta_x, obj_y + delta_y, obj_z + delta_z)

    # Is the block next to clicked-block, available to be created?
    if new_coords not in world or world[new_coords].type == 'air':
        addBlock(currentBlock, *new_coords)


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
    global base, world
    print("working")

    build_world()
    setup_base_keys()
    setup_fog()
    setup_pause_menu(base, world, addBlock)
    base.run()


if __name__ == '__main__':
    run_the_world()
