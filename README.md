# pd-emu -- a Panic Playdate emulator

## Dependencies
To (eventually) run, you will need:
- **For graphics, sound, etc.:** [pygame/pygame](https://github.com/pygame/pygame) (no changes needed)
- **For emulation of games written in C:** [qilingframework/qiling](https://github.com/qilingframework/qiling) (no changes needed)
- **For emulation of games written in Lua:** [scoder/lupa](https://github.com/scoder/lupa) (custom build with my forked Lua)
- **For parsing Playdate's Lua headers:** my fork of Lua 5.4.0 which adds Playdate support (will be added soon)

## Running
You can't actually run this emulator now (since I have yet to add the Playdate API).

What you _can_ do now is dump Playdate applications (directories with a PDX extension) from the command line.

## Dumping Playdate applications/games
To dump a PDX:
- `cd` to the root directory of this repo
- `python3 loaders/pdx.py (path to PDX) (dump location)`

Tested and working for all the system apps in the 1.12.3 SDK (latest version as of this writing).

## Decompiling the Lua files
See my fork of [unluac](https://sourceforge.net/p/unluac/) for instructions.
