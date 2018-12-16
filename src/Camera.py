"""
Assumes that a default Camera has been created, then
moves it around via assigned keys, with the Mouse to change
direction of looking.

Note that horizontal-movement, is relative to the forward-vector (where
the Mouse is pointing). So your X/Y coordinates change differently, depending
on where you're facing. But the vertical-movement always moves relative to
the Z-axis, so regardless of your facing, you move up/down on the Z-axis only.

Only difference I see in 'absolute' vs 'relative' mousing - 'absolute'
lets the mouse move outside the screen (where movement-reports stop, since
the Window doesn't have the mouse any more), and 'relative' reports movement
to any extent, no limits (but the cursor is fixed in the center of the screen,
the only thing reported is the motion of the mouse).

"""

from math import cos, sin, radians

import direct.showbase.ShowBaseGlobal as BG

# noinspection PyUnresolvedReferences
from panda3d.core import WindowProperties

from src.Keys import TRANSLATE_DATA


def move_camera(the_base, the_keys_hit):

    rotate_camera(the_base)

    some_keys_hit = [key_name for key_name, key_val in the_keys_hit.items() if key_val]
    if not some_keys_hit:
        return

    my_cam = the_base.camera

    up_down_keys_hit = [key_name for key_name, key_val in the_keys_hit.items()
                        if key_val and TRANSLATE_DATA.get(key_name, {}).get('axis', '') == 'z']
    sideways_keys_hit = [key_name for key_name, key_val in the_keys_hit.items()
                         if key_val and TRANSLATE_DATA.get(key_name, {}).get('axis', 'z') != 'z']

    if up_down_keys_hit:
        foo = (my_cam.getX(), my_cam.getY(), my_cam.getZ())
        change_loc = calculate_vertical_offset(TRANSLATE_DATA, up_down_keys_hit, foo)
        my_cam.setPos(change_loc)

        return

    if sideways_keys_hit:
        foo = (my_cam.getX(), my_cam.getY(), my_cam.getZ())
        the_h = my_cam.getH()
        change_loc = calculate_horizontal_offset(TRANSLATE_DATA, the_h, sideways_keys_hit, foo)
        my_cam.setPos(change_loc)

        return


def rotate_camera(the_base):
    """ Mouse returns a set of X/Y coordinates, with 0/0 in the center of the screen.
        Convert X into an H-rotation, and Y into a P-rotation.
        Mouse should be in Relative-mode.
    """

    rotation_scale = 100

    my_cam = the_base.camera
    m_node = the_base.mouseWatcherNode

    x = m_node.getMouseX() * the_base.win.getXSize()
    y = m_node.getMouseY() * the_base.win.getYSize()

    move_dir_H = get_abs_value(x, 2)
    move_dir_P = get_abs_value(y, 2)

    dt = BG.globalClock.getDt()
    old_H = my_cam.getH()
    old_P = my_cam.getP()

    new_H = old_H + move_dir_H * dt * rotation_scale
    new_H = lock_to_zero(new_H)
    my_cam.setH(new_H)

    new_P = old_P + move_dir_P * dt * rotation_scale
    new_P = lock_to_zero(new_P)
    my_cam.setP(new_P)

    # print(f"rotate_camera.camera: [{x}, {y}, -]. [h: {old_H:3.1f} -> {old_H:3.1f}, dt = {dt:3.1f}]")

    the_base.win.movePointer(0, int(the_base.win.getXSize() / 2), int(the_base.win.getYSize() / 2))


def setup_camera(the_base, the_world, camera_start_coords):

    the_base.camLens.setFar(256)
    the_base.camera.setPos(camera_start_coords)
    # the_base.camera.setHpr(0, -37, 0)  # This didn't seem to work, so just point at a Block.
    foo = the_world[(0, 0, 8)].model
    the_base.camera.lookAt(foo)

    # x, y, z = the_base.camera.getX(), the_base.camera.getY(), the_base.camera.getZ()
    # h, p, r = the_base.camera.getR(), the_base.camera.getP(), the_base.camera.getR()
    # print(f"setup_camera.camera = [{x}, {y}, {z}]: [{h:3.1f}, {p:3.1f}, {r:3.1f}]")

    # Turn off Mouse
    props = WindowProperties()
    props.setCursorHidden(True)
    props.setMouseMode(WindowProperties.M_relative)
    the_base.win.requestProperties(props)


def calculate_vertical_offset(mutators, arrow_keys_hit, some_coords):

    dt = BG.globalClock.getDt()
    change_bits = (0, 0, 0)

    some_arrow = arrow_keys_hit[0]
    arrow_data = mutators[some_arrow]
    new_scale = arrow_data['scale'] * dt
    add_H = arrow_data['dir'][0] * new_scale
    add_P = arrow_data['dir'][1] * new_scale
    add_R = arrow_data['dir'][2] * new_scale
    change_bits = (change_bits[0] + add_H, change_bits[1] + add_P, change_bits[2] + add_R)

    final_bits = (change_bits[0] + some_coords[0],
                  change_bits[1] + some_coords[1],
                  change_bits[2] + some_coords[2])

    # print(f"\ninitial coords = [{some_coords}]\nchange_bits = [{change_bits}]\nfinal_bits = [{final_bits}]\n")

    return final_bits


def calculate_horizontal_offset(mutators, rotate_H, arrow_keys_hit, cur_coords):
    """ Only handles X/Y coordinates - computes them based on current Rotation.
    :param mutators:
    :param rotate_H:
    :param arrow_keys_hit:
    :param cur_coords:
    :return:
    """

    dt = BG.globalClock.getDt()
    base_x, base_y = 0, 0

    # Unlike the up/down motion, it's possible for two movement-keys to be held
    # down at once (say "forward" and "sideways"), so combine all of the vector-changes
    # from every key that's being hit.
    for some_arrow in arrow_keys_hit:
        arrow_data = mutators[some_arrow]
        new_scale = arrow_data['scale'] * dt
        base_x = base_x + arrow_data['dir'][0] * new_scale
        base_y = base_y + arrow_data['dir'][1] * new_scale

    rotate_x, rotate_y = rotate_vector(base_x, base_y, rotate_H)

    final_bits = (rotate_x + cur_coords[0], rotate_y + cur_coords[1], cur_coords[2])

    # print(f"\ninitial coords = [{cur_coords}]\nrotate_bits = [{rotate_x}, {rotate_y}]\nfinal_bits = [{final_bits}]\n")

    return final_bits


def rotate_vector(x, y, angle):
    """ Finally! A chance to use some of that trigger-nometry!
    https://stackoverflow.com/questions/20023209/function-for-rotating-2d-objects
    :param x:
    :param y:
    :param angle:
    :return:
    """

    theta = radians(angle % 360)
    new_x = x * cos(theta) - y * sin(theta)
    new_y = x * sin(theta) + y * cos(theta)

    # print("\n\tpre-x = %s, pre-y = %s" % (x, y))
    # print("\n\tpost-x = %s, post-y = %s, angle = %s, theta = %s" % (new_x, new_y, angle, theta))

    return new_x, new_y


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


