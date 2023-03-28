# pd-emu - a Panic Playdate emulator

## ...but why?
Yes, Panic already provides a piece of software called Playdate Simulator, but...
- It's geared towards testing your own games rather than playing other people's.
- It can't run device builds of games written in C.
- It doesn't allow communication via the simulated Playdate's USB port.

I decided to try and fix this with new, _open-source_ software.

## Getting the repo
1. Choose your favorite Python package manager to install these:
	- For dumping PNG/GIF images: [Pillow](https://github.com/python-pillow/Pillow)
	- For graphics, sound, etc.: [pygame](https://github.com/pygame/pygame)
2. Run `git clone --recursive https://github.com/scratchminer/pd-emu.git` to clone this repo and its submodules.
3. `cd lupa && make` should build the forks of both Lupa and Lua without having to run `setup.py` directly.
4. Use your favorite Python package manager to install the wheel in the `lupa/dist` directory.

## Running
You can't actually run this emulator now (since I have yet to add the Playdate API).

What you _can_ do now is dump Playdate applications (directories with a PDX extension) from the command line.

## Dumping Playdate applications/games
To dump a PDX:
- `cd` to the root directory of this repo
- `python3 -m loaders.pdx (path to PDX) (dump location)`

Tested and working for all the system apps in the 1.13.2 SDK (latest version as of this writing), as well as every game in Season 1.

## Decompiling the Lua files
See [my fork of unluac](https://github.com/scratchminer/unluac) for instructions.

--------------------
2023 scratchminer

Not affiliated with Panic at all, just a neat little side project I've been doing for a while.
