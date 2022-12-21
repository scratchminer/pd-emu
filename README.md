# pd-emu - a Panic Playdate emulator

## ...but why?
Yes, Panic already provides a piece of software called Playdate Simulator, but...
- It's geared towards testing your own games rather than playing other people's.
- It can't run builds of games written in C.
- It doesn't allow communication via the simulated Playdate's USB port.

I decided to try and fix this with new, _open-source_ software.

## Dependencies
To (eventually) run, you will need:
- **For graphics, sound, etc.:** [pygame/pygame](https://github.com/pygame/pygame) (no changes needed)
- **For emulation of games written in C:** [qilingframework/qiling](https://github.com/qilingframework/qiling) (no changes needed)
- **For emulation of games written in Lua:** [scoder/lupa](https://github.com/scratchminer/lupa) (forked version with custom build of Lua)
- **For parsing Playdate's Lua headers:** [lua/lua](https://github.com/scratchminer/lua54) (forked version with header and opcode patches)

## Running
You can't actually run this emulator now (since I have yet to add the Playdate API).

What you _can_ do now is dump Playdate applications (directories with a PDX extension) from the command line.

## Dumping Playdate applications/games
To dump a PDX:
- `cd` to the root directory of this repo
- `python3 loaders/pdx.py (path to PDX) (dump location)`

Tested and working for all the system apps in the 1.12.3 SDK (latest version as of this writing).

## Decompiling the Lua files
See [my fork of unluac](https://github.com/scratchminer/unluac) for instructions.

--------------------
2022 scratchminer

Not affiliated with Panic at all, just a neat little side project I've been doing for a while.
