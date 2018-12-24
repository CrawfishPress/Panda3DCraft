"""
I need a *what* An *inverted sphere*? What in tarnation is an
inverted sphere, and where do I find one?

This files writes out a .BAM file of a Skybox, pasting together
six PNG files into a crude SkySphere.

Note there are several hardcoded full filepaths here - I had a
lot of problems with relative-paths, they were embedded in the BAM
file, so I couldn't see what they were (well, without using bam2egg).

I finally wound up putting the BAM file in the same directory as main.py,
which is kludgy, but works consistently. Someday I need to work on
that relative-pathing.

There's a tool for constructing Skymaps at http://alexcpeterson.com/spacescape/,
but it doesn't run on Linux, so I just put together half a dozen manually-
generated PNGs. Which I actually did using PaintShop Pro 7 on Windows, oddly - I
can't stand GIMP.

https://www.panda3d.org/manual/index.php/Cube_Maps
"""

import sys
from pathlib import Path

# noinspection PyPackageRequirements
from direct.showbase.ShowBase import ShowBase
import panda3d.core as core

# This is needed to handle all cases of relative-imports. There may
# be a better way, but so far I haven't found it.
TOP_DIR = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, TOP_DIR)

BOX_PATH = '/home/crawford/repos/Panda3DCraft/gfx/sky/box_#.png'
SPHERE_PATH = '/home/crawford/repos/Panda3DCraft/gfx/sky/InvertedSphere.egg'
BOX_OUT = '/home/crawford/repos/Panda3DCraft/sky_box.bam'

Base = ShowBase()


def build_the_box():
    stage_defaults = core.TextureStage.getDefault()

    texture = Base.loader.loadCubeMap(BOX_PATH)

    sphere = Base.loader.loadModel(SPHERE_PATH)
    sphere.setTexGen(stage_defaults, core.TexGenAttrib.MWorldPosition)
    sphere.setTexProjector(stage_defaults, Base.render, sphere)
    sphere.setTexPos(stage_defaults, 0, 0, 0)
    sphere.setTexScale(stage_defaults, 0.5)
    sphere.setTexture(texture)
    sphere.setLightOff()
    sphere.setScale(1000)

    # To preview it:
    # sphere.reparentTo(Base.render)
    # Base.run()

    # To write it:
    res = sphere.writeBamFile(BOX_OUT)
    print(f"wrote file [{BOX_OUT}] with result {res}")


if __name__ == '__main__':
    build_the_box()
