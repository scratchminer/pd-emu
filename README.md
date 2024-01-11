# pd-emu - a Panic Playdate emulator

## ...but why?
Yes, Panic already provides a piece of software called Playdate Simulator, but...
- It's geared towards testing your own games rather than playing other people's.
- It can't run device builds of games written in C.
- It doesn't allow communication via the simulated Playdate's USB port.

I decided to try and fix this with new, *open-source* software.

## Getting the repo
1. Run `git clone --recursive https://github.com/scratchminer/pd-emu.git` to clone this repo and its submodules.
2. `pip install -r requirements.txt` should install all the dependencies except Lupa and Lua.
3. `cd lupa && make` should build the forks of both Lupa and Lua without having to run `setup.py`.
4. Use your favorite Python package manager to install the wheel in the `lupa/dist` directory.

## Running
You can't actually run this emulator now (since I have yet to add the Playdate API).

What you *can* do now is dump Playdate applications (directories with a PDX extension) from the command line.

## Dumping Playdate applications/games
To dump a PDX:
- `cd` to the root directory of this repo
- `python3 -m loaders.pdx (path to PDX) (dump location)`

## Decompiling the Lua files
See [my fork of unluac](https://github.com/scratchminer/unluac) for instructions.

---
2024 scratchminer

Not affiliated with Panic at all, just a neat little side project I've been doing for a while.
