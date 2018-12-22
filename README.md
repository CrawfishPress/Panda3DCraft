# Panda3DCraft
This is a Fork of a Clone of Minecraft made in Panda3D. Very early WIP.

This fork has been updated for Python 3.6+ and Panda3D 1.10+.
Plus a lot of refactoring, how movement works, etc. I can't speak for the goals
of the original repo, but my goal for this fork, is just to play around
with Panda3D, learn the basics of it.

## Installation/Starting

 - create a virtual environment with Python 3.6+
 - *pip install -r requirements.txt*
 - *python main.py --play --level --block grass*

## Command-line options
 - -l, --level, level the ground, no noisy-generation
 - -b, --block, set block-type for initial terrain-generation, default='dirt'
 - -p, --play, play the game - any cmd-option will also play

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
 - *b* - enters/exits the Block-selection menu
 - *r* - resets camera-location to starting location

 - *ESC* - enters/exits the Pause/Save-Load screen

#### Camera-Movement Mode
 - *a/d* - move left/right
 - *w/s* - move forward/backward
 - *z/x* - move downward/upward

#### Block-Control Mode
 - *right-mouse-click* - places a Block of the current Type
 - *left-mouse-click* - deletes the Block where the mouse is pointing

## Known Glitches
 - When you exit Block-Selection or Pause-screen, you stay in Mouse-mode, whether
   you were there before or not (it doesn't restore the previous mode).
 - When you type in a Save-game name - the key-mappings aren't suspended, so typing
   'rho' for a name, resets the view. Wups...
 - If you delete the front-corner block, and hit *r* (reset), things go boom...

## TODO
 - Done: Fix the Pause-Screen - it broke after I changed how Camera-handling worked
 - Done: Change Block-type selection to a visible Menu of Blocks, rather than a number.
 - Done: Added level-ground option
 - Combine the two Modes, so you can move around and add blocks at the same time.
 - Handle re-setting the Camera to look at the closest Block that has not been *deleted*.
 - Refactor out all of the *global* variables.
 - Add a third-person view, so Camera can see the person moving around.
 - Add flowing water.
 - Add torches, play with lighting.
 - Add a setup.py, and put on PyPi.org?
