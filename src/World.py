from contextlib import suppress
import random

from noise import snoise2

from src.BlockClass import BlockClass

verboseLogging = True


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


