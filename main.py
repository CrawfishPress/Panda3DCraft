from contextlib import suppress
import random

from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from noise import snoise2

from BlockClass import BLOCKS, BlockClass
from menu import PauseScreen

Core.loadPrcFile('config/general.prc')

if __debug__:  # True unless Python is started with -O
    print(f"debug-mode on")
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
    fancy_rendering = False

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

    if fancy_rendering:
        # Use a 512x512 resolution shadow map
        slight.setShadowCaster(True, 512, 512)
        # Enable the shader generator for the receiving nodes
        MY_BASE.render.setShaderAuto()

    TRAVERSER = Core.CollisionTraverser()
    COLLISION_HANDLER = Core.CollisionHandlerQueue()

    picker_node = Core.CollisionNode('mouseRay')
    picker_np = MY_BASE.camera.attachNewNode(picker_node)
    picker_node.setFromCollideMask(Core.GeomNode.getDefaultCollideMask())
    PICKER_RAY = Core.CollisionRay()
    picker_node.addSolid(PICKER_RAY)
    TRAVERSER.addCollider(picker_np, COLLISION_HANDLER)


def write_ground_blocks():

    block_type = CURRENT_BLOCK

    want_new_generation = False
    fill_world = False

    octaves_elev = 5
    octaves_rough = 2
    octaves_detail = 1
    freq = 16.0 * octaves_elev

    for x in range(0, 16):
        for y in range(0, 16):
            amplitude = random.randrange(0.0, 5.0)
            if want_new_generation:
                z = max(min(int(snoise2(x / freq, y / freq, octaves_elev) + (
                    snoise2(x / freq, y / freq, octaves_rough) *
                    snoise2(x / freq, y / freq, octaves_detail)) * 64 + 64), 128), 0)
                add_block(block_type, x, y, z)
            else:
                z = max((int(snoise2(x / freq, y / freq, 5) * amplitude) + 8), 0)
                add_block(block_type, x, y, z)
            if fill_world:
                for height in range(0, z + 1):
                    add_block(block_type, x, y, height)

            if verboseLogging:
                print(f"Generated [{block_type}]: [{x}, {y}, {z}]")


def add_block(block_type, x, y, z):
    global MY_BASE, MY_WORLD

    with suppress(KeyError, AttributeError):
        MY_WORLD[(x, y, z)].cleanup()

    MY_WORLD[(x, y, z)] = BlockClass(block_type, MY_BASE, x, y, z)


def handle_pick(right_click=False):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE, MY_WORLD, PAUSE_MENU

    if PAUSE_MENU.is_paused:
        return

    if not MY_BASE.mouseWatcherNode.hasMouse():
        return

    mpos = MY_BASE.mouseWatcherNode.getMouse()
    PICKER_RAY.setFromLens(MY_BASE.camNode, mpos.getX(), mpos.getY())

    TRAVERSER.traverse(MY_BASE.render)
    if COLLISION_HANDLER.getNumEntries() <= 0:
        return

    COLLISION_HANDLER.sortEntries()
    picked_obj = COLLISION_HANDLER.getEntry(0).getIntoNodePath()
    picked_obj = picked_obj.findNetTag('blockTag')
    if picked_obj.isEmpty():
        return

    if right_click:
        add_block_object(picked_obj, COLLISION_HANDLER.getEntry(0).getIntoNodePath())
    else:
        remove_block_object(picked_obj)


def hotbar_select(slot):

    global CURRENT_BLOCK, CUR_BLOCK_TEXT

    next_block_name = [block_name for block_name, block_val in BLOCKS.items()
                       if block_val['hotkey'] == slot][0]
    CURRENT_BLOCK = next_block_name
    CUR_BLOCK_TEXT["text"] = next_block_name

    if verboseLogging:
        print(f"Selected hotbar slot {slot}")
        print(f"Current block: {next_block_name}")


def setup_base_keys():
    global MY_BASE

    MY_BASE.accept('mouse1', handle_pick)
    MY_BASE.accept('mouse3', handle_pick, extraArgs=[True])
    MY_BASE.accept('escape', PAUSE_MENU.pause)

    for one_block in BLOCKS.values():
        MY_BASE.accept(str(one_block['hotkey']), hotbar_select, extraArgs=[one_block['hotkey']])


def remove_block_object(obj):

    if verboseLogging:
        print(f"Left clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}]")

    # We have to add the Block in order to destroy it...
    add_block('air', obj.getX(), obj.getY(), obj.getZ())


def add_block_object(obj, node_path):

    if verboseLogging:
        print(f"Right clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}],"
              f" attempting to place [{CURRENT_BLOCK}]")

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
        add_block(CURRENT_BLOCK, *new_coords)


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
    global MY_BASE, MY_WORLD, PAUSE_MENU
    print("building world...")

    PAUSE_MENU = PauseScreen(MY_BASE, MY_WORLD, add_block)
    setup_lighting()
    write_ground_blocks()
    setup_base_keys()
    setup_fog()

    MY_BASE.run()


if __name__ == '__main__':
    run_the_world()
