"""
I need a *what* An *inverted sphere*? What in tarnation is an
inverted sphere, and where do I find one?

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

BOX_PATH = TOP_DIR + '/gfx/sky/box_#.png'
SPHERE_PATH = TOP_DIR + '/gfx/sky/InvertedSphere.egg'
SPHERE_OUT = TOP_DIR + '/gfx/sky/sky_box.bam'
SPHERE_OUT2 = '/home/crawford/Projects/panda/new/sky_box.bam'

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
    sphere.setScale(10000)

    # To preview it:
    sphere.reparentTo(Base.render)
    Base.run()

    # To write it:
    sphere.writeBamFile(SPHERE_OUT)
    # result = sphere.writeBamFile(SPHERE_OUT2)  # Scale(5000) worked
    # print(f"Wrote BAM file with result [{result}]")


if __name__ == '__main__':
    build_the_box()
