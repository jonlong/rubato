# SPDX-FileCopyrightText: 2021 John Park for Adafruit Industries
# SPDX-License-Identifier: MIT
# Rubato — Ableton MIDI Controller MacroPad
# In Ableton, use MIDI Map mode to assign controls to the MacroPad
import board
from adafruit_macropad import MacroPad
import displayio
import terminalio
from adafruit_simplemath import constrain
from adafruit_display_text import label
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

macropad = MacroPad()

TITLE_TEXT = "Rubato"
print(TITLE_TEXT)

# --- Button definitions: (name, note, channel, color) ---
# Channels are 0-indexed (channel 10 in Ableton = 9 here, channel 11 = 10, channel 1 = 0)
PADS = [
    ("prev_loc",      18, 9,  0x00FF40),  # 0  - light green
    ("next_loc",      19, 9,  0x00FF40),  # 1  - light green
    ("add_loc",       16, 9,  0x006620),  # 2  - dark green
    ("expand_L",      20, 9,  0xCC5500),  # 3  - dark orange
    ("expand_R",      23, 9,  0xCC5500),  # 4  - dark orange
    ("loop",          24, 9,  0xFF8800),  # 5  - orange
    ("contract_L",    21, 9,  0xFFDD00),  # 6  - yellow
    ("contract_R",    22, 9,  0xFFDD00),  # 7  - yellow
    ("follow",         8, 10, 0x40C0FF),  # 8  - light blue
    ("nudge_L",       25, 9,  0x9900FF),  # 9  - purple
    ("nudge_R",       26, 9,  0x9900FF),  # 10 - purple
    ("pause/play",    15, 9,  0xFF0000),  # 11 - red
]

# Pads that should fire momentarily (NoteOn+NoteOff on press, nothing on release)
MOMENTARY_PADS = {3, 4, 6, 7, 9, 10}  # expand_L, expand_R, contract_L, contract_R, nudge_L, nudge_R

# --- Encoder modes ---
ENC_MODES = [
    {"name": "tempo", "cc": 70, "channel": 0, "relative": False},   # Ableton ch 1, absolute
    {"name": "jogger", "cc": 71, "channel": 0, "relative": True},   # Ableton ch 1, relative — change CC after mapping
]
enc_mode = 0  # start in tempo mode
CC_OFFSET = 20
cc_position = CC_OFFSET
last_position = 0

# --- MIDI setup ---
midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    out_channel=0
)

# --- NeoPixel setup ---
BRIGHT = 0.125
DIM = 0.05
macropad.pixels.brightness = BRIGHT
for i, pad in enumerate(PADS):
    macropad.pixels[i] = pad[3]
macropad.pixels.show()

# --- Display setup ---
display = board.DISPLAY
screen = displayio.Group()
display.root_group = screen
FONT = terminalio.FONT


# --- Icon definitions (8x8, 1-bit, each row is a byte, MSB = left) ---
ICON_DATA = [
    # 0: prev_loc ◀
    (0x08, 0x18, 0x38, 0x78, 0x38, 0x18, 0x08, 0x00),
    # 1: next_loc ▶
    (0x40, 0x60, 0x70, 0x78, 0x70, 0x60, 0x40, 0x00),
    # 2: add_loc ⚑
    (0xF8, 0xF8, 0xF8, 0x80, 0x80, 0x80, 0x80, 0x00),
    # 3: expand_L [
    (0xF0, 0x80, 0x80, 0x80, 0x80, 0x80, 0xF0, 0x00),
    # 4: expand_R ]
    (0x0F, 0x01, 0x01, 0x01, 0x01, 0x01, 0x0F, 0x00),
    # 5: loop ↻
    (0x3A, 0x4C, 0x80, 0x80, 0x80, 0x81, 0x42, 0x3C),
    # 6: contract_L )
    (0x80, 0x40, 0x20, 0x10, 0x10, 0x20, 0x40, 0x80),
    # 7: contract_R (
    (0x01, 0x02, 0x04, 0x08, 0x08, 0x04, 0x02, 0x01),
    # 8: follow ◎
    (0x3C, 0x42, 0x99, 0xA5, 0xA5, 0x99, 0x42, 0x3C),
    # 9: nudge_L «
    (0x00, 0x28, 0x50, 0xA0, 0x50, 0x28, 0x00, 0x00),
    # 10: nudge_R »
    (0x00, 0x28, 0x14, 0x0A, 0x14, 0x28, 0x00, 0x00),
    # 11: pause/play ▶‖
    (0x8A, 0xCA, 0xEA, 0xFA, 0xEA, 0xCA, 0x8A, 0x00),
]

icon_palette = displayio.Palette(2)
icon_palette[0] = 0x000000
icon_palette[1] = 0xFFFFFF
icon_palette.make_transparent(0)

def make_icon(data):
    bmp = displayio.Bitmap(8, 8, 2)
    for y in range(8):
        for x in range(8):
            if data[y] & (1 << (7 - x)):
                bmp[x, y] = 1
    return bmp

# Icon grid with labels — 3 columns x 4 rows
ICON_LABELS = [
    "prv", "nxt", "add",
    "exp", "exp", "lp",
    "con", "con", "fol",
    "ndg", "ndg", "pp",
]
icon_x = [5, 44, 83]
icon_y = [2, 14, 26, 38]

for i, data in enumerate(ICON_DATA):
    col = i % 3
    row = i // 3
    tg = displayio.TileGrid(make_icon(data), pixel_shader=icon_palette,
                            x=icon_x[col], y=icon_y[row])
    screen.append(tg)
    lbl = label.Label(FONT, text=ICON_LABELS[i], color=0xFFFFFF,
                      x=icon_x[col] + 10, y=icon_y[row] + 4)
    screen.append(lbl)

# Encoder info on display
enc_label = label.Label(FONT, text="tempo", color=0xFFFFFF, x=5, y=58)
screen.append(enc_label)

# Pixel meter bar
METER_W = 70
METER_H = 7
meter_bmp = displayio.Bitmap(METER_W, METER_H, 2)
meter_palette = displayio.Palette(2)
meter_palette[0] = 0x000000
meter_palette[1] = 0xFFFFFF

# Draw border
for x in range(METER_W):
    meter_bmp[x, 0] = 1
    meter_bmp[x, METER_H - 1] = 1
for y in range(METER_H):
    meter_bmp[0, y] = 1
    meter_bmp[METER_W - 1, y] = 1

def update_meter(val, max_val=127):
    inner_w = METER_W - 4
    fill = round(val / max_val * (inner_w - 1)) + 1
    for x in range(2, 2 + inner_w):
        lit = 1 if (x - 2) < fill else 0
        for y in range(2, METER_H - 2):
            meter_bmp[x, y] = lit


update_meter(CC_OFFSET)
meter_tg = displayio.TileGrid(meter_bmp, pixel_shader=meter_palette, x=52, y=55)
screen.append(meter_tg)

# Text display for jogger mode (hidden off-screen initially)
jog_text = label.Label(FONT, text="", color=0xFFFFFF, x=52, y=-20)
screen.append(jog_text)

# --- Main loop ---
while True:
    key_event = macropad.keys.events.get()

    if not key_event:
        # Handle encoder rotation
        mode = ENC_MODES[enc_mode]
        position = macropad.encoder
        if position != last_position:
            if mode["relative"]:
                # Relative: send 1 for CW, 127 for CCW per tick
                delta = position - last_position
                for _ in range(abs(delta)):
                    val = 127 if delta > 0 else 1
                    midi.send(ControlChange(mode["cc"], val), channel=mode["channel"])
                jog_text.text = ">>>" if delta > 0 else "<<<"
            else:
                # Absolute: send 0-127, clamp virtual position to prevent overrun
                delta = position - last_position
                cc_position = int(constrain(cc_position + delta, 0, 127))
                midi.send(ControlChange(mode["cc"], cc_position), channel=mode["channel"])
                update_meter(cc_position)
            last_position = position

        # Handle encoder switch — toggle mode
        macropad.encoder_switch_debounced.update()
        if macropad.encoder_switch_debounced.pressed:
            enc_mode = (enc_mode + 1) % len(ENC_MODES)
            mode = ENC_MODES[enc_mode]
            enc_label.text = mode["name"]
            if mode["relative"]:
                meter_tg.y = -20
                jog_text.y = 58
                jog_text.text = "---"
            else:
                jog_text.y = -20
                meter_tg.y = 55
                update_meter(cc_position)
            print("Encoder mode:", mode["name"])

        continue

    num = key_event.key_number
    pad = PADS[num]
    note = pad[1]
    channel = pad[2]

    if key_event.pressed:
        midi.send(NoteOn(note, 127), channel=channel)
        macropad.pixels[num] = 0xFFFFFF  # flash white on press
        macropad.pixels.show()
        print("Note", note, "ch", channel + 1, "-> ON")

    if key_event.released:
        if num in MOMENTARY_PADS:
            # Send another NoteOn to untoggle the M4L button
            midi.send(NoteOn(note, 127), channel=channel)
        midi.send(NoteOff(note, 0), channel=channel)
        macropad.pixels[num] = pad[3]  # restore color
        macropad.pixels.show()
        print("Note", note, "ch", channel + 1, "-> OFF")
