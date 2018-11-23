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


def setup_lighting(the_base):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER
    fancy_rendering = False

    alight = Core.AmbientLight('alight')
    alight.setColor(Core.VBase4(0.6, 0.6, 0.6, 1))
    alnp = the_base.render.attachNewNode(alight)
    the_base.render.setLight(alnp)
    slight = Core.Spotlight('slight')
    slight.setColor(Core.VBase4(1, 1, 1, 1))
    lens = Core.PerspectiveLens()
    slight.setLens(lens)
    slnp = the_base.render.attachNewNode(slight)
    slnp.setPos(8, -9, 128)
    slnp.setHpr(0, 270, 0)
    the_base.render.setLight(slnp)

    if fancy_rendering:
        # Use a 512x512 resolution shadow map
        slight.setShadowCaster(True, 512, 512)
        # Enable the shader generator for the receiving nodes
        the_base.render.setShaderAuto()

    TRAVERSER = Core.CollisionTraverser()
    COLLISION_HANDLER = Core.CollisionHandlerQueue()

    picker_node = Core.CollisionNode('mouseRay')
    picker_np = the_base.camera.attachNewNode(picker_node)
    picker_node.setFromCollideMask(Core.GeomNode.getDefaultCollideMask())
    PICKER_RAY = Core.CollisionRay()
    picker_node.addSolid(PICKER_RAY)
    TRAVERSER.addCollider(picker_np, COLLISION_HANDLER)


def write_ground_blocks(block_type, the_base):

    the_world = {}
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
                add_block(block_type, x, y, z, the_world, the_base)
            else:
                z = max((int(snoise2(x / freq, y / freq, 5) * amplitude) + 8), 0)
                add_block(block_type, x, y, z, the_world, the_base)
            if fill_world:
                for height in range(0, z + 1):
                    add_block(block_type, x, y, height, the_world, the_base)

            if verboseLogging:
                print(f"Generated [{block_type}]: [{x}, {y}, {z}]")

    return the_world


def add_block(block_type, x, y, z, the_world, the_base):

    with suppress(KeyError, AttributeError):
        the_world[(x, y, z)].cleanup()

    the_world[(x, y, z)] = BlockClass(block_type, the_base, x, y, z)


def handle_pick(right_click=False):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE, MY_WORLD, PAUSE_MENU, CURRENT_BLOCK

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
        add_block_object(CURRENT_BLOCK, picked_obj, COLLISION_HANDLER.getEntry(0).getIntoNodePath(),
                         MY_WORLD, MY_BASE)
    else:
        remove_block_object(picked_obj, MY_WORLD, MY_BASE)


def hotbar_select(slot):

    global CURRENT_BLOCK, CUR_BLOCK_TEXT

    next_block_name = [block_name for block_name, block_val in BLOCKS.items()
                       if block_val['hotkey'] == slot][0]
    CURRENT_BLOCK = next_block_name
    CUR_BLOCK_TEXT["text"] = next_block_name

    if verboseLogging:
        print(f"Selected hotbar slot {slot}")
        print(f"Current block: {next_block_name}")


def setup_base_keys(the_base):

    global PAUSE_MENU

    the_base.accept('mouse1', handle_pick)
    the_base.accept('mouse3', handle_pick, extraArgs=[True])
    the_base.accept('escape', PAUSE_MENU.pause)

    for one_block in BLOCKS.values():
        the_base.accept(str(one_block['hotkey']), hotbar_select, extraArgs=[one_block['hotkey']])


def remove_block_object(obj, the_world, the_base):

    if verboseLogging:
        print(f"Left clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}]")

    # We have to add the Block in order to destroy it...
    add_block('air', obj.getX(), obj.getY(), obj.getZ(), the_world, the_base)


def add_block_object(cur_block, obj, node_path, the_world, the_base):

    if verboseLogging:
        print(f"Right clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}],"
              f" attempting to place [{cur_block}]")

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
    if new_coords not in the_world or the_world[new_coords].type == 'air':
        add_block(cur_block, *new_coords, the_world, the_base)


def setup_fog(the_base, cur_block):

    global CUR_BLOCK_TEXT

    fog = Core.Fog("fog")
    fog.setColor(0.5294, 0.8078, 0.9215)
    fog.setExpDensity(0.015)
    the_base.render.setFog(fog)
    the_base.camLens.setFar(256)

    the_base.setFrameRateMeter(True)

    CUR_BLOCK_TEXT = DirectLabel(text=cur_block, text_fg=(1, 1, 1, 1),
                                 frameColor=(0, 0, 0, 0),
                                 parent=the_base.aspect2d, scale=0.05, pos=(0, 0, -0.95))


def run_the_world():

    global MY_BASE, MY_WORLD, PAUSE_MENU
    print("building world...")

    MY_WORLD = write_ground_blocks(CURRENT_BLOCK, MY_BASE)
    PAUSE_MENU = PauseScreen(MY_BASE, MY_WORLD, add_block)

    setup_lighting(MY_BASE)
    setup_base_keys(MY_BASE)
    setup_fog(MY_BASE, CURRENT_BLOCK)

    MY_BASE.run()


if __name__ == '__main__':
    run_the_world()
