import sys

from panda3d.core import *
import panda3d.core as Core
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase

# noinspection PyUnresolvedReferences
from panda3d.core import WindowProperties

from src.BlockClass import BLOCKS
from src.World import write_ground_blocks, add_block
from src.Camera import setup_camera, rotate_camera
from src.menu import PauseScreen

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
MY_BASE = None
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


def setup_tasks():
    global MY_BASE, MOUSE_ACTIVE

    MY_BASE.taskMgr.add(camera_rotator, "Moving_Object", appendTask=True)


def camera_rotator(task):
    """ This is somewhat kludgy - originally I had the taskMgr directly call rotate_camera(),
        and passing it the parameters. But it turns out that the parameters don't *change*
        (of course), and I needed MOUSE_ACTIVE to be updated.
    :param task:
    :return:
    """
    global MY_BASE, MOUSE_ACTIVE

    m_node = MY_BASE.mouseWatcherNode

    if MOUSE_ACTIVE or not m_node.hasMouse():
        return task.cont

    rotate_camera(MY_BASE)
    return task.cont


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
    print("reset.block[0,0,8].xyz = %s, %s, %s" % (x, y, z))
    MY_BASE.camera.setHpr(0, -37, 0)
    MY_BASE.camera.lookAt(foo)
    x, y, z = MY_BASE.camera.getX(), MY_BASE.camera.getY(), MY_BASE.camera.getZ()
    h, p, r = MY_BASE.camera.getR(), MY_BASE.camera.getP(), MY_BASE.camera.getR()
    print(f"camera.rs = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

    # MY_BASE.win.movePointer(0, int(MY_BASE.win.getXSize() / 2), int(MY_BASE.win.getYSize() / 2))


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
#        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
    else:
        print("Mouse now OFF")
#        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)

    MY_BASE.win.requestProperties(props)


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


def run_the_world():

    global MY_BASE, MY_WORLD, PAUSE_MENU
    print("building world...")

    MY_BASE = ShowBase()
    MY_WORLD = write_ground_blocks(CURRENT_BLOCK, MY_BASE)
    PAUSE_MENU = PauseScreen(MY_BASE, MY_WORLD, add_block)

    MY_BASE.disableMouse()
    setup_lighting(MY_BASE)

    setup_base_keys()
    setup_fog(MY_BASE, CURRENT_BLOCK)
    setup_camera(MY_BASE, MY_WORLD, CAMERA_START_COORDS)
    setup_tasks()

    MY_BASE.run()


if __name__ == '__main__':
    run_the_world()
