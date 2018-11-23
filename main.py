from contextlib import suppress
import random

from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from noise import snoise2

from BlockClass import BLOCKS, BlockClass
from menu import setup_pause_menu, is_paused, pause

Core.loadPrcFile('config/general.prc')

if __debug__:  # True unless Python is started with -O
    print("debug-mode on")
    Core.loadPrcFile('config/dev.prc')

verboseLogging = True

PICKER_RAY = None
TRAVERSER = None
COLLISION_HANDLER = None
PAUSE_MENU = None

CURRENT_BLOCK = 'dirt'
CUR_BLOCK_TEXT = None

MY_WORLD = {}
MY_BASE = ShowBase()


def setup_lighting():
    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE
    fancyRendering = False

    alight = Core.AmbientLight('alight')
    alight.setColor(Core.VBase4(0.6, 0.6, 0.6, 1))
    alnp = MY_BASE.render.attachNewNode(alight)
    MY_BASE.render.setLight(alnp)
    slight = Core.Spotlight('slight')
    slight.setColor(Core.VBase4(1, 1, 1, 1))
    lens = Core.PerspectiveLens()
    slight.setLens(lens)
    slnp = MY_BASE.render.attachNewNode(slight)
    slnp.setPos(8, -9, 128)
    slnp.setHpr(0, 270, 0)
    MY_BASE.render.setLight(slnp)

    if fancyRendering:
        # Use a 512x512 resolution shadow map
        slight.setShadowCaster(True, 512, 512)
        # Enable the shader generator for the receiving nodes
        MY_BASE.render.setShaderAuto()

    TRAVERSER = Core.CollisionTraverser()
    COLLISION_HANDLER = Core.CollisionHandlerQueue()

    pickerNode = Core.CollisionNode('mouseRay')
    pickerNP = MY_BASE.camera.attachNewNode(pickerNode)
    pickerNode.setFromCollideMask(Core.GeomNode.getDefaultCollideMask())
    PICKER_RAY = Core.CollisionRay()
    pickerNode.addSolid(PICKER_RAY)
    TRAVERSER.addCollider(pickerNP, COLLISION_HANDLER)


def write_ground_blocks():

    blockType = CURRENT_BLOCK

    wantNewGeneration = False
    fillWorld = False

    octavesElev = 5
    octavesRough = 2
    octavesDetail = 1
    freq = 16.0 * octavesElev

    for x in range(0, 16):
        for y in range(0, 16):
            amplitude = random.randrange(0.0, 5.0)
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


def addBlock(blockType, x, y, z):
    global MY_BASE, MY_WORLD

    with suppress(KeyError, AttributeError):
        MY_WORLD[(x, y, z)].cleanup()

    MY_WORLD[(x, y, z)] = BlockClass(blockType, MY_BASE, x, y, z)


def handlePick(right_click=False):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE, MY_WORLD

    if is_paused():
        return

    if not MY_BASE.mouseWatcherNode.hasMouse():
        return

    mpos = MY_BASE.mouseWatcherNode.getMouse()
    PICKER_RAY.setFromLens(MY_BASE.camNode, mpos.getX(), mpos.getY())

    TRAVERSER.traverse(MY_BASE.render)
    if COLLISION_HANDLER.getNumEntries() <= 0:
        return

    COLLISION_HANDLER.sortEntries()
    pickedObj = COLLISION_HANDLER.getEntry(0).getIntoNodePath()
    pickedObj = pickedObj.findNetTag('blockTag')
    if pickedObj.isEmpty():
        return

    if right_click:
        addBlockObject(pickedObj, COLLISION_HANDLER.getEntry(0).getIntoNodePath())
    else:
        removeBlockObject(pickedObj)


def hotbarSelect(slot):

    global CURRENT_BLOCK, CUR_BLOCK_TEXT

    next_block_name = [block_name for block_name, block_val in BLOCKS.items()
                       if block_val['hotkey'] == slot][0]
    CURRENT_BLOCK = next_block_name
    CUR_BLOCK_TEXT["text"] = next_block_name

    if verboseLogging:
        print("Selected hotbar slot %d" % slot)
        print("Current block: %s" % next_block_name)


def setup_base_keys():
    global MY_BASE

    MY_BASE.accept('mouse1', handlePick)
    MY_BASE.accept('mouse3', handlePick, extraArgs=[True])
    MY_BASE.accept('escape', pause)

    for one_block in BLOCKS.values():
        MY_BASE.accept(str(one_block['hotkey']), hotbarSelect, extraArgs=[one_block['hotkey']])


def removeBlockObject(obj):

    if verboseLogging:
        print("Left clicked a block at [%d, %d, %d]" % (obj.getX(), obj.getY(), obj.getZ()))

    # We have to add the Block in order to destroy it...
    addBlock('air', obj.getX(), obj.getY(), obj.getZ())


def addBlockObject(obj, node_path):

    if verboseLogging:
        print("Right clicked a block at [%d, %d, %d], attempting to place [%s]" % (
            obj.getX(), obj.getY(), obj.getZ(), CURRENT_BLOCK))

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
    if new_coords not in MY_WORLD or MY_WORLD[new_coords].type == 'air':
        addBlock(CURRENT_BLOCK, *new_coords)


def setup_fog():

    global CUR_BLOCK_TEXT, MY_BASE

    fog = Core.Fog("fog")
    fog.setColor(0.5294, 0.8078, 0.9215)
    fog.setExpDensity(0.015)
    MY_BASE.render.setFog(fog)
    MY_BASE.camLens.setFar(256)

    MY_BASE.setFrameRateMeter(True)

    CUR_BLOCK_TEXT = DirectLabel(text=CURRENT_BLOCK, text_fg=(1, 1, 1, 1),
                                 frameColor=(0, 0, 0, 0),
                                 parent=MY_BASE.aspect2d, scale=0.05, pos=(0, 0, -0.95))


def run_the_world():
    global MY_BASE, MY_WORLD
    print("working")

    setup_lighting()
    write_ground_blocks()
    setup_base_keys()
    setup_fog()
    setup_pause_menu(MY_BASE, MY_WORLD, addBlock)

    MY_BASE.run()


if __name__ == '__main__':
    run_the_world()
