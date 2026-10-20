# Notes for working on Broadside Bay

- Any new 3D model (.glb, e.g. from TRELLIS) must go through `python3 tools/prepare_model.py IN.glb www/models/NAME.glb` before it is used. It strips built-in lights/cameras (the first model shipped with 4 bright lights that washed every ship and island white), removes glow, and shrinks the texture.
- After adding a model, compare a screenshot of the same scene with and without the model on screen, so nothing else in the game changes colour.
