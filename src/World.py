"""
Purpose: Builds a World dictionary of randomly-generated Block-types. I have no
idea how it works - something to do with Noise...
"""

from contextlib import suppress
import random

from noise import snoise2

from src.BlockClass import BlockClass

MAX_WIDTH = 16
MAX_LENGTH = 16


def write_ground_blocks(the_base, block_type, level_ground, scale=1.0):

    the_world = {}
    want_new_generation = False
    fill_world = False

    octaves_elev = 5
    octaves_rough = 2
    octaves_detail = 1
    freq = 16.0 * octaves_elev

    if level_ground:
        for x in range(0, MAX_WIDTH):
            for y in range(0, MAX_LENGTH):
                add_block(block_type, x, y, 8, the_world, the_base, scale)
        return the_world

    for x in range(0, MAX_WIDTH):
        for y in range(0, MAX_LENGTH):
            amplitude = random.randrange(0.0, 5.0)
            if want_new_generation:
                z = max(min(int(snoise2(x / freq, y / freq, octaves_elev) + (
                    snoise2(x / freq, y / freq, octaves_rough) *
                    snoise2(x / freq, y / freq, octaves_detail)) * 64 + 64), 128), 0)
                add_block(block_type, x, y, z, the_world, the_base, scale)
            else:
                z = max((int(snoise2(x / freq, y / freq, 5) * amplitude) + 8), 0)
                add_block(block_type, x, y, z, the_world, the_base, scale)
            if fill_world:
                for height in range(0, z + 1):
                    add_block(block_type, x, y, height, the_world, the_base, scale)

            # print(f"Generated [{block_type}]: [{x}, {y}, {z}]")

    return the_world


def add_block(block_type, x, y, z, the_world, the_base, scale=1.0):

    with suppress(KeyError, AttributeError):
        the_world[(x, y, z)].cleanup()

    new_block = BlockClass(block_type, the_base, x, y, z, scale)
    the_world[(x, y, z)] = new_block

    return new_block


def remove_block_object(node_path, the_world, the_base):

    # print(f"Left clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}]")
    obj = node_path.findNetTag('blockTag')

    # We have to add the Block in order to destroy it...
    add_block('air', obj.getX(), obj.getY(), obj.getZ(), the_world, the_base)


def get_new_block_coords(node_path):

    moves = {
        'west': {'delta_x': -1, 'delta_y': 0, 'delta_z': 0, 'clicked': node_path.hasNetTag('westTag')},
        'east': {'delta_x': 1, 'delta_y': 0, 'delta_z': 0, 'clicked': node_path.hasNetTag('eastTag')},
        'south': {'delta_x': 0, 'delta_y': -1, 'delta_z': 0, 'clicked': node_path.hasNetTag('southTag')},
        'north': {'delta_x': 0, 'delta_y': 1, 'delta_z': 0, 'clicked': node_path.hasNetTag('northTag')},
        'top': {'delta_x': 0, 'delta_y': 0, 'delta_z': 1, 'clicked': node_path.hasNetTag('topTag')},
        'bot': {'delta_x': 0, 'delta_y': 0, 'delta_z': -1, 'clicked': node_path.hasNetTag('botTag')},
        }

    clicked = [one_block for one_block in moves.values() if one_block['clicked']]
    # noinspection PyUnreachableCode
    if __debug__:
        assert len(clicked) == 1

    obj = node_path.findNetTag('blockTag')
    # print(f"Right clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}],"
    #       f" attempting to place [{cur_block}]")
    # print(f"obj = {type(obj)}:{str(obj)}, node_path = {type(node_path)}:{str(node_path)}")

    new_coords = get_new_coords(obj, clicked[0])
    return new_coords


def is_new_block_free(new_coords, the_world):

    if new_coords not in the_world or the_world[new_coords].type == 'air':
        return True

    return False


def get_new_coords(some_obj, clicked_data):

    old_x, old_y, old_z = some_obj.getX(), some_obj.getY(), some_obj.getZ()
    delta_x, delta_y, delta_z = clicked_data['delta_x'], clicked_data['delta_y'], clicked_data['delta_z']

    new_coords = (old_x + delta_x, old_y + delta_y, old_z + delta_z)

    return new_coords
