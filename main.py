from contextlib import suppress
import random
import sys

from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
import direct.showbase.ShowBaseGlobal as BG

# noinspection PyUnresolvedReferences
from panda3d.core import WindowProperties

from noise import snoise2

from BlockClass import BLOCKS, BlockClass
from menu import PauseScreen

Core.loadPrcFile('config/general.prc')

# noinspection PyUnreachableCode
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
MOUSE_ACTIVE = False

MY_WORLD = {}
MY_BASE = ShowBase()
CAMERA_START_COORDS = (-10, -10, 30)


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

    # if fancy_rendering:
    #     # Use a 512x512 resolution shadow map
    #     slight.setShadowCaster(True, 512, 512)
    #     # Enable the shader generator for the receiving nodes
    #     the_base.render.setShaderAuto()

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


def setup_tasks():
    global MY_BASE

    MY_BASE.taskMgr.add(rotate_camera, "Moving_Object", appendTask=True)


def handle_click(right_click=False):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE, MY_WORLD, PAUSE_MENU, CURRENT_BLOCK, MOUSE_ACTIVE

    if PAUSE_MENU.is_paused:
        return

    if not MY_BASE.mouseWatcherNode.hasMouse():
        return

    if not MOUSE_ACTIVE:
        return

    x, y, z = MY_BASE.camera.getX(), MY_BASE.camera.getY(), MY_BASE.camera.getZ()
    h, p, r = MY_BASE.camera.getR(), MY_BASE.camera.getP(), MY_BASE.camera.getR()
    print(f"handle_click.camera = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

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


def setup_base_keys():

    global PAUSE_MENU, MY_BASE

    MY_BASE.accept('mouse1', handle_click)
    MY_BASE.accept('mouse3', handle_click, extraArgs=[True])
    # MY_BASE.accept('escape', PAUSE_MENU.pause)
    MY_BASE.accept('escape', sys.exit)

    # Keys that need de-bouncing
    MY_BASE.accept("m", toggle_mouse, ["m", True])
    MY_BASE.accept("m-up", toggle_mouse, ["m", False])
    MY_BASE.accept("r", reset_stuff, ["r", True])
    MY_BASE.accept("r-up", reset_stuff, ["r", False])

    for one_block in BLOCKS.values():
        MY_BASE.accept(str(one_block['hotkey']), hotbar_select, extraArgs=[one_block['hotkey']])


def reset_stuff(key, value):
    """ De-bouncing the 'r' key
    """
    global MY_BASE, MY_WORLD

    if key != 'r' or not value:
        return

    # my_cam = MY_BASE.camera
    # my_cam.reparentTo(MY_BASE.render)
    # my_cam.setPos(CAMERA_START_COORDS)
    # some_block = MY_WORLD[(0, 0, 8)].model
    # my_cam.lookAt(some_block)

    MY_BASE.camera.setPos(CAMERA_START_COORDS)
    foo = MY_WORLD[(0, 0, 8)].model  # Be aware this block can be *deleted*
    x, y, z = foo.getX(), foo.getY(), foo.getZ()
    print("foo.xyz = %s, %s, %s" % (x, y, z))
    MY_BASE.camera.setHpr(0, -37, 0)
    MY_BASE.camera.lookAt(foo)
    x, y, z = MY_BASE.camera.getX(), MY_BASE.camera.getY(), MY_BASE.camera.getZ()
    h, p, r = MY_BASE.camera.getR(), MY_BASE.camera.getP(), MY_BASE.camera.getR()
    print(f"camera.rs = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

#    MY_BASE.win.movePointer(0, int(MY_BASE.win.getXSize() / 2), int(MY_BASE.win.getYSize() / 2))


def toggle_mouse(key, value):
    """ I handle this outside of the original update_key() function, because I'm not
        sure otherwise how to handle key debouncing. If you hold down "m", you get a stream
        of "m" events, but when you release the key, you get an "m" event instead of an "m-up"
        event.
    """
    global MY_BASE, MOUSE_ACTIVE

    if key != 'm' or not value:
        return

    MOUSE_ACTIVE = not MOUSE_ACTIVE
    print("switching mouse.active to %s" % MOUSE_ACTIVE)

    props = WindowProperties()
    if MOUSE_ACTIVE:
        print("Mouse now ON")
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
    else:
        print("Mouse now OFF")
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)

    MY_BASE.win.requestProperties(props)


def rotate_camera(task):
    """ Mouse returns a set of X/Y coordinates, with 0/0 in the center of the screen.
        Convert X into an H-rotation, and Y into a P-rotation.
        Only if Mouse is in Relative-mode.
    """
    global MOUSE_ACTIVE, MY_BASE
    rotation_scale = 100

    my_cam = MY_BASE.camera
    m_node = MY_BASE.mouseWatcherNode

    if MOUSE_ACTIVE or not m_node.hasMouse():
        return task.cont

    x = m_node.getMouseX() * MY_BASE.win.getXSize()
    y = m_node.getMouseY() * MY_BASE.win.getYSize()

    move_dir_H = get_abs_value(x, 2)
    move_dir_P = get_abs_value(y, 2)

    dt = BG.globalClock.getDt()
    old_H = my_cam.getH()
    old_P = my_cam.getP()

    new_H = old_H + move_dir_H * dt * rotation_scale
    new_H = lock_to_zero(new_H)
    my_cam.setH(new_H)

    new_P = old_P + move_dir_P * dt * rotation_scale
    new_P = lock_to_zero(new_P)  # This didn't work as expected...
    my_cam.setP(new_P)

    # print(f"rotate_camera.camera: [{x}, {y}, -]. [h: {old_H:3.1f} -> {old_H:3.1f}, dt = {dt:3.1f}]")

    MY_BASE.win.movePointer(0, int(MY_BASE.win.getXSize() / 2), int(MY_BASE.win.getYSize() / 2))

    return task.cont


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
    # noinspection PyUnreachableCode
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

    global CUR_BLOCK_TEXT, MY_WORLD, CAMERA_START_COORDS

    fog = Core.Fog("fog")
    fog.setColor(0.5294, 0.8078, 0.9215)
    fog.setExpDensity(0.015)
    the_base.render.setFog(fog)

    the_base.setFrameRateMeter(True)

    CUR_BLOCK_TEXT = DirectLabel(text=cur_block, text_fg=(1, 1, 1, 1),
                                 frameColor=(0, 0, 0, 0),
                                 parent=the_base.aspect2d, scale=0.05, pos=(0, 0, -0.95))


def setup_camera(the_base):

    global MY_WORLD, CAMERA_START_COORDS

    the_base.camLens.setFar(256)
    the_base.camera.setPos(CAMERA_START_COORDS)
    the_base.camera.setHpr(0, -37, 0)
    foo = MY_WORLD[(0, 0, 8)].model
    the_base.camera.lookAt(foo)
    x, y, z = the_base.camera.getX(), the_base.camera.getY(), the_base.camera.getZ()
    h, p, r = the_base.camera.getR(), the_base.camera.getP(), the_base.camera.getR()
    print(f"setup_camera.camera = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")


def get_abs_value(test_val, epsilon):

    new_val = 0

    if test_val > epsilon:
        new_val = -1

    if test_val < -epsilon:
        new_val = 1

    return new_val


def lock_to_zero(test_val, lock_angle=360):

    if test_val > lock_angle or test_val < -lock_angle:
        return 0

    return test_val


def run_the_world():

    global MY_BASE, MY_WORLD, PAUSE_MENU
    print("building world...")

    MY_WORLD = write_ground_blocks(CURRENT_BLOCK, MY_BASE)
    PAUSE_MENU = PauseScreen(MY_BASE, MY_WORLD, add_block)

    MY_BASE.disableMouse()
    setup_lighting(MY_BASE)

    setup_base_keys()
    setup_fog(MY_BASE, CURRENT_BLOCK)
    setup_camera(MY_BASE)
    setup_tasks()

    MY_BASE.run()


if __name__ == '__main__':
    run_the_world()
