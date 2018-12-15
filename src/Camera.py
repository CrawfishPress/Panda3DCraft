import direct.showbase.ShowBaseGlobal as BG


def rotate_camera(the_base):
    """ Mouse returns a set of X/Y coordinates, with 0/0 in the center of the screen.
        Convert X into an H-rotation, and Y into a P-rotation.
        Only if Mouse is in Relative-mode.
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
    new_P = lock_to_zero(new_P)  # This didn't work as expected...
    my_cam.setP(new_P)

    # print(f"rotate_camera.camera: [{x}, {y}, -]. [h: {old_H:3.1f} -> {old_H:3.1f}, dt = {dt:3.1f}]")

    the_base.win.movePointer(0, int(the_base.win.getXSize() / 2), int(the_base.win.getYSize() / 2))


def setup_camera(the_base, the_world, camera_start_coords):

    the_base.camLens.setFar(256)
    the_base.camera.setPos(camera_start_coords)
    the_base.camera.setHpr(0, -37, 0)
    foo = the_world[(0, 0, 8)].model
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


