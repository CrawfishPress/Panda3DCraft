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


def write_ground_blocks(block_type, the_base):

    the_world = {}
    want_new_generation = False
    fill_world = False

    octaves_elev = 5
    octaves_rough = 2
    octaves_detail = 1
    freq = 16.0 * octaves_elev

    for x in range(0, MAX_WIDTH):
        for y in range(0, MAX_LENGTH):
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

            # print(f"Generated [{block_type}]: [{x}, {y}, {z}]")

    return the_world


def add_block(block_type, x, y, z, the_world, the_base):

    with suppress(KeyError, AttributeError):
        the_world[(x, y, z)].cleanup()

    the_world[(x, y, z)] = BlockClass(block_type, the_base, x, y, z)


def remove_block_object(obj, the_world, the_base):

    # print(f"Left clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}]")

    # We have to add the Block in order to destroy it...
    add_block('air', obj.getX(), obj.getY(), obj.getZ(), the_world, the_base)


def add_block_object(cur_block, obj, node_path, the_world, the_base):

    # print(f"Right clicked a block at [{obj.getX()}, {obj.getY()}, {obj.getZ()}],"
    #       f" attempting to place [{cur_block}]")

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
