# Rubato

A MIDI controller for Ableton Live built with an [Adafruit MacroPad RP2040](https://www.adafruit.com/product/5128) and a companion Max for Live device. Designed as a practice and transcription tool, with cue-point-based loop navigation for working through sections of a track.

## What it does

The MacroPad sends MIDI notes and CC messages to Ableton. The Max for Live device (`Rubato.amxd`) receives those messages and translates them into loop manipulation commands via the Live API.

### Pad layout (3x4 grid)

```
 prev_loc   next_loc   add_loc
 expand_L   expand_R   loop
 contract_L contract_R follow
 nudge_L    nudge_R    pause/play
```

- **prev/next_loc** -- jump between cue points
- **add_loc** -- add a cue point
- **expand/contract L/R** -- resize the loop from either side (momentary)
- **loop** -- toggle loop on/off
- **follow** -- toggle follow mode (loop tracks playback position across cues)
- **nudge L/R** -- shift the loop left or right by one cue (momentary)
- **pause/play** -- transport toggle

### Encoder

Press to toggle between two modes:

- **Tempo** -- absolute CC (0-127), shown as a meter bar on the display
- **Jogger** -- relative CC, sends increment/decrement per tick

## Project structure

```
macrocontroller/   CircuitPython firmware (deployed to the MacroPad)
  code.py          Main controller code
  lib/             Adafruit CircuitPython libraries

macropad/          Development copy / alternate layout
  code.py          Variant of the controller code

m4l/               Max for Live device
  Rubato.amxd      The M4L device (drop into an Ableton track)
  logic.js         JS logic for cue-based loop manipulation
  poly-observer.maxpat
```

## Setup

1. Install [CircuitPython](https://circuitpython.org/board/adafruit_macropad_rp2040/) on the MacroPad
2. Copy the contents of `macrocontroller/` (or `macropad/`) to the `CIRCUITPY` drive
3. Drop `m4l/Rubato.amxd` onto a track in Ableton Live
4. Use Ableton's MIDI Map mode to bind the MacroPad's notes/CCs to the desired controls

## Credits

- MacroPad starter code based on [John Park's Adafruit MacroPad examples](https://learn.adafruit.com/macropad-hotkeys)
- Max for Live logic by [Sebastien Vaillancourt (SebVe)](https://sebve.com)
