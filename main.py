"""
Purpose: learning Panda3D, by building a random block-world, that might
bear a passing resemblance to Minecraft.

Forked under MIT license, from:

https://github.com/kengleason/Panda3DCraft

"""

import argparse
from argparse import RawTextHelpFormatter
import random
import sys

from panda3d.core import *
import panda3d.core as core
# noinspection PyPackageRequirements
from direct.gui.DirectGui import *
# noinspection PyPackageRequirements
from direct.showbase.ShowBase import ShowBase

# noinspection PyUnresolvedReferences
from panda3d.core import WindowProperties

from src.BlockMenu import BlockMenu
from src.Keys import setup_base_keys
from src.World import write_ground_blocks, remove_block_object, add_block_object
from src.Camera import setup_camera, move_camera
from src.menu import PauseScreen

core.loadPrcFile('config/general.prc')

# noinspection PyUnreachableCode
if __debug__:  # True unless Python is started with -O
    print(f"debug-mode on")
    core.loadPrcFile('config/dev.prc')

# TODO: kill all of these Global variables

PICKER_RAY = None
TRAVERSER = None
COLLISION_HANDLER = None
PAUSE_MENU = None
BLOCK_MENU = None

CUR_BLOCK_TEXT = None
MOUSE_ACTIVE = False

MY_WORLD = {}
MY_BASE = None
CAMERA_START_COORDS = (-10, -10, 30)

ERROR_LIST = (
    "I *told* you not to delete that block!",
    "Well, here's another nice mess you've gotten me into...",
    "There's one in every crowd...",
    "Now with 30% fewer bugs - except this one!",
    "He's dead, Jim",
    "Sorry about that, Chief",
    "Or was it the *red* wire?",
    "Dave, I can feel my mind going. Dave?",
    "It is better to burn out, than to fa~~~~~~~ <connection broken>",
    "And now, for a final word from our sponsor...",
    "A life is like a garden - perfect moments can be had, but not preserved, except in memory.",
)


class UserError(Exception):
    pass


def setup_lighting(the_base):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER
    # fancy_rendering = False

    alight = core.AmbientLight('alight')
    alight.setColor(core.VBase4(0.6, 0.6, 0.6, 1))
    alnp = the_base.render.attachNewNode(alight)
    the_base.render.setLight(alnp)
    slight = core.Spotlight('slight')
    slight.setColor(core.VBase4(1, 1, 1, 1))
    lens = core.PerspectiveLens()
    slight.setLens(lens)
    slnp = the_base.render.attachNewNode(slight)
    slnp.setPos(8, -9, 128)
    slnp.setHpr(0, 270, 0)
    the_base.render.setLight(slnp)

    # I have no idea what this does, so it must not be important...
    # if fancy_rendering:
    #     # Use a 512x512 resolution shadow map
    #     slight.setShadowCaster(True, 512, 512)
    #     # Enable the shader generator for the receiving nodes
    #     the_base.render.setShaderAuto()

    TRAVERSER = core.CollisionTraverser()
    COLLISION_HANDLER = core.CollisionHandlerQueue()

    picker_node = core.CollisionNode('mouseRay')
    picker_np = the_base.camera.attachNewNode(picker_node)
    picker_node.setFromCollideMask(core.GeomNode.getDefaultCollideMask())
    PICKER_RAY = core.CollisionRay()
    picker_node.addSolid(PICKER_RAY)
    TRAVERSER.addCollider(picker_np, COLLISION_HANDLER)


def setup_fog(the_base, cur_block):

    global CUR_BLOCK_TEXT

    fog = core.Fog("fog")
    fog.setColor(0.5294, 0.8078, 0.9215)
    fog.setExpDensity(0.015)
    the_base.render.setFog(fog)

    the_base.setFrameRateMeter(True)

    CUR_BLOCK_TEXT = DirectLabel(text=cur_block, text_fg=(1, 1, 1, 1),
                                 frameColor=(0, 0, 0, 0),
                                 parent=the_base.aspect2d, scale=0.05, pos=(0, 0, -0.95))


def setup_tasks(the_base):

    the_base.taskMgr.add(camera_mangler, "Moving_Camera", appendTask=True)


def camera_mangler(task):
    """ This is somewhat kludgy - originally I had the taskMgr directly call rotate_camera(),
        and passing it the parameters. But it turns out that the parameters don't *change*
        (of course), and I needed MOUSE_ACTIVE to be updated.
    """
    global MY_BASE, MOUSE_ACTIVE

    m_node = MY_BASE.mouseWatcherNode

    if MOUSE_ACTIVE or not m_node.hasMouse():
        return task.cont

    move_camera(MY_BASE)

    return task.cont


def handle_click(right_click=False):

    global PICKER_RAY, TRAVERSER, COLLISION_HANDLER, MY_BASE, MY_WORLD, PAUSE_MENU, BLOCK_MENU, MOUSE_ACTIVE

    if PAUSE_MENU.is_paused:
        return

    if not MY_BASE.mouseWatcherNode.hasMouse():
        return

    if not MOUSE_ACTIVE:
        return

    # x, y, z = MY_BASE.camera.getX(), MY_BASE.camera.getY(), MY_BASE.camera.getZ()
    # h, p, r = MY_BASE.camera.getR(), MY_BASE.camera.getP(), MY_BASE.camera.getR()
    # print(f"handle_click.camera = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

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
        add_block_object(BLOCK_MENU.active_block_type, picked_obj,
                         COLLISION_HANDLER.getEntry(0).getIntoNodePath(),
                         MY_WORLD, MY_BASE)
    else:
        remove_block_object(picked_obj, MY_WORLD, MY_BASE)


def call_pause_screen():
    """ This is a little kludgy, since I activate the Mouse, if needed,
        so the Pause screen can work, but don't de-activate it if it was
        already inactive. Hey, the player can just hit the 'm' key again...
    """
    global MOUSE_ACTIVE, MY_BASE, PAUSE_MENU

    if not MOUSE_ACTIVE:
        toggle_mouse('m', True)

    PAUSE_MENU.pause()


def call_toggle_blocks(key, value):
    global MY_BASE, MOUSE_ACTIVE, BLOCK_MENU, CUR_BLOCK_TEXT

    if key != 'b' or not value:
        return

    if not MOUSE_ACTIVE:
        toggle_mouse('m', True)

    BLOCK_MENU.toggle_menu()

    # If menu turned off, set the new block-type
    if not BLOCK_MENU.is_visible:
        cur_block_name = BLOCK_MENU.active_block_type
        CUR_BLOCK_TEXT["text"] = cur_block_name


def reset_stuff(key, value):
    """ De-bouncing the 'r' key
    """
    global MY_BASE, MY_WORLD, CAMERA_START_COORDS

    if key != 'r' or not value:
        return

    # Point Camera at some base Block
    MY_BASE.camera.setPos(CAMERA_START_COORDS)
    try:
        foo = MY_WORLD[(0, 0, 8)].model  # Be aware this block can be *deleted*
    except AttributeError:
        raise UserError(random.choice(ERROR_LIST))

    # x, y, z = foo.getX(), foo.getY(), foo.getZ()
    # print("reset.block[0,0,8].xyz = %s, %s, %s" % (x, y, z))
    MY_BASE.camera.setHpr(0, -37, 0)
    MY_BASE.camera.lookAt(foo)

    # x, y, z = MY_BASE.camera.getX(), MY_BASE.camera.getY(), MY_BASE.camera.getZ()
    # h, p, r = MY_BASE.camera.getR(), MY_BASE.camera.getP(), MY_BASE.camera.getR()
    # print(f"camera.rs = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

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
    # print("switching mouse.active to %s" % MOUSE_ACTIVE)

    props = WindowProperties()
    if MOUSE_ACTIVE:
        # print("Mouse now ON")
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
    else:
        # print("Mouse now OFF")
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)

    MY_BASE.win.requestProperties(props)


def run_the_world(cmd_args):

    global MY_BASE, MY_WORLD, PAUSE_MENU, BLOCK_MENU

    if cmd_args.level:
        level_ground = True
        print(f"\nBuilding world with level ground, block-type = [{cmd_args.block}]")
    else:
        level_ground = False
        print(f"\nBuilding world with noisy ground, block-type = [{cmd_args.block}]")

    MY_BASE = ShowBase()
    MY_BASE.disableMouse()

    cur_block = cmd_args.block
    BLOCK_MENU = BlockMenu(MY_BASE, cur_block)

    MY_WORLD = write_ground_blocks(MY_BASE, cur_block, level_ground)

    PAUSE_MENU = PauseScreen(MY_BASE, MY_WORLD)

    setup_lighting(MY_BASE)
    setup_fog(MY_BASE, cur_block)
    setup_camera(MY_BASE, MY_WORLD, CAMERA_START_COORDS)
    setup_base_keys(MY_BASE, call_pause_screen, handle_click,
                    toggle_mouse, call_toggle_blocks, reset_stuff)
    setup_tasks(MY_BASE)

    MY_BASE.run()


def handle_cmd_options():

    usage = """
    Usage: Play around in a simple block-world, that bears a passing resemblance
    to Minecraft. You can:
     - select from one of *nine* different block-types
     - add/remove blocks
     - save/load a game
     - move around the world with the keyboard/mouse (mouse rotates view only)

    r = resets location/camera view - hit this at start of game, if view is empty
    m = toggles between movement (invisible mouse), and block-placement (visible mouse)
    b = toggles block-selection menu
    ESC = toggles pause/save-game screen

    a/s/d/w = moves around horizontally
    z/x = moves up/down (or was it down, then up?)
    """

    hp = lambda prog: RawTextHelpFormatter(prog, max_help_position=50, width=120)
    parser = argparse.ArgumentParser(description=usage, formatter_class=hp)

    parser.add_argument('-v', '--verbose', action="store_true", help='verbose debugging statements - TBD')
    parser.add_argument('-l', '--level', action="store_true", help='level the ground, no noisy-generation')
    parser.add_argument('-b', '--block', default='grass', help='set block-type for initial terrain-generation')
    parser.add_argument('-p', '--play', action="store_true", help='play the game - any cmd-option will also play')
    cmd_args = parser.parse_args()

    # You would think an empty argument list would *default* to printing help, but no...
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return cmd_args


if __name__ == '__main__':
    args = handle_cmd_options()
    run_the_world(args)
