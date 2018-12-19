# Panda3DCraft
This is a Fork of a Clone of Minecraft made in Panda3D. Very early WIP.

This fork has been updated for Python 3.6+ and Panda3D 1.10+.
Plus a lot of refactoring, how movement works, etc. I can't speak for the goals
of the original repo, but my goal for this fork, is just to play around
with Panda3D, learn the basics of it.

## Installation/Starting

 - create a virtual environment with Python 3.6+
 - *pip install -r requirements.txt*
 - *python main.py*

## Usage
 - hit the *r* (reset) key, if necessary - sometimes the view doesn't setup right. Weird...
 - the game starts out in Camera-Movement mode, so if you want to use the Mouse to,
   say, expand the Window to full-screen, hit the *m* key to toggle into that mode.
 - whatever you do, *don't delete the front-corner Block* - if you hit the *r* (reset)
   key, it turns the camera to look at that Block. (I should probably fix that...)  
 - use *a/s/d/w* to move around, and *z/z* to move down/up

### CONTROLS

I revised the original control-scheme, specifically splitting it into
two Modes: Camera-Movement, and Block-Control/removal. I haven't really looked at how the
block-picker/Collider stuff works, and it was just easier to make two separate modes.

#### General keys
 - *m* - toggle between Camera-Movement, and Block-Control
 - *r* - resets camera-location to starting location
 - *ESC* - quits game (the Pause/Save-Load screen was assigned to that, now is disabled)

 - *1-9* change the currently-select Block type

#### Camera-Movement Mode
 - *a/d* - move left/right
 - *w/s* - move forward/backward
 - *z/x* - move downward/upward

#### Block-Control Mode
 - *right-mouse-click* - places a Block of the current Type
 - *left-mouse-click* - deletes the Block where the mouse is pointing

## TODO
 - Done: Fix the Pause-Screen - it broke after I changed how Camera-handling worked
 - Combine the two Modes, so you can move around and add blocks at the same time.
 - Change Block-type selection to a visible Menu of Blocks, rather than a number.
 - Handle re-setting the Camera to look at the closest Block, if it has been *deleted*.
 - Refactor out all of the *global* variables.
 - Add a third-person view, so Camera can see the person moving around.
