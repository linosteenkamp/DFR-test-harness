#!/usr/bin/env python3
"""Build the harness wiring diagrams.

This script is the master copy. It writes:
  docs/wiring/wiring-diagram.html   the full page (all diagrams, themed light/dark)
  docs/wiring/*.svg                 one standalone SVG per diagram (embedded in HARDWARE.md)

Edit the drawing functions below, run `python3 docs/wiring/build.py`, and commit
the regenerated files together with the wiring change they describe.
"""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- primitives

GND_DEF = (
    '<defs><g id="gnd">'
    '<line x1="0" y1="0" x2="0" y2="8" stroke="currentColor" stroke-width="1.6"/>'
    '<line x1="-9" y1="8" x2="9" y2="8" stroke="currentColor" stroke-width="1.6"/>'
    '<line x1="-6" y1="12" x2="6" y2="12" stroke="currentColor" stroke-width="1.6"/>'
    '<line x1="-3" y1="16" x2="3" y2="16" stroke="currentColor" stroke-width="1.6"/>'
    "</g></defs>"
)


class D:
    """Collects shapes and text for one diagram."""

    def __init__(self):
        self.parts = []

    # shapes are emitted inside a stroke group; cls selects the colour layer
    def _g(self, inner, cls=None, sw=1.6, dash=None):
        c = f' class="{cls}"' if cls else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<g{c} fill="none" stroke="currentColor" stroke-width="{sw}"{d}>{inner}</g>'
        )

    def rect(self, x, y, w, h, cls=None, dash=None, rx=3, sw=1.6):
        self._g(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>', cls, sw, dash)

    def line(self, *pts, cls=None, dash=None, sw=1.6):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self._g(f'<polyline points="{p}"/>', cls, sw, dash)

    def poly(self, pts, cls=None, fill=False):
        p = " ".join(f"{x},{y}" for x, y in pts)
        f = ' fill="currentColor"' if fill else ""
        c = f' class="{cls}"' if cls else ""
        self.parts.append(
            f'<g{c} fill="none" stroke="currentColor" stroke-width="1.6"><polygon points="{p}"{f}/></g>'
        )

    def dot(self, x, y, cls=None, r=3):
        c = f' class="{cls}"' if cls else ""
        self.parts.append(f'<g{c}><circle cx="{x}" cy="{y}" r="{r}" fill="currentColor"/></g>')

    def gnd(self, x, y, cls=None):
        c = f' class="{cls}"' if cls else ""
        self.parts.append(f'<g{c}><use href="#gnd" xlink:href="#gnd" x="{x}" y="{y}"/></g>')

    def text(self, x, y, s, cls=None, anchor="start", layer=None):
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        c = f' class="{cls}"' if cls else ""
        t = f'<text x="{x}" y="{y}"{a}{c}>{escape(s)}</text>'
        if layer:
            t = f'<g class="{layer}">{t}</g>'
        self.parts.append(t)

    # composite symbols
    def res_h(self, x, y, w=44, cls=None):
        """Horizontal resistor centred on y, from x to x+w (IEC box)."""
        self.rect(x, y - 7, w, 14, cls=cls, rx=1)

    def res_v(self, x, y, h=36, cls=None):
        """Vertical resistor centred on x, from y to y+h."""
        self.rect(x - 7, y, 14, h, cls=cls, rx=1)

    def fuse(self, x, y, w=50, cls=None):
        self.rect(x, y - 8, w, 16, cls=cls, rx=1)
        self.line((x, y), (x + w, y), cls=cls, sw=1)

    def relay(self, x, y, label, cls=None):
        """Changeover contact: COM at (x,y), NC at (x+70,y), NO at (x+70,y-24).
        Drawn at rest (blade on NC)."""
        self.line((x, y), (x + 66, y - 4), cls=cls)            # blade
        self.line((x + 70, y - 24), (x + 84, y - 24), cls=cls)  # NO stub
        for px, py in ((x, y), (x + 70, y), (x + 70, y - 24)):
            self.dot(px, py, cls=cls, r=3)
        self.text(x - 4, y + 16, "COM", "t-muted", "middle")
        self.text(x + 78, y + 16, "NC", "t-muted")
        self.text(x + 90, y - 20, "NO", "t-muted")
        if label:
            self.text(x + 112, y - 20, label, "t-strong", layer=cls)

    def diode_up(self, x, y_anode, y_cathode, cls=None):
        """Diode on a vertical line, anode below, cathode above (y_cathode < y_anode)."""
        mid = (y_anode + y_cathode) / 2
        self.line((x, y_anode), (x, mid + 7), cls=cls)
        self.poly([(x - 8, mid + 7), (x + 8, mid + 7), (x, mid - 6)], cls=cls)
        self.line((x - 8, mid - 6), (x + 8, mid - 6), cls=cls)
        self.line((x, mid - 6), (x, y_cathode), cls=cls)

    def svg_body(self):
        return GND_DEF + "\n".join(self.parts)


# ---------------------------------------------------------------- diagrams

def bench_overview():
    d = D()
    N = "new"
    # LAN bus
    d.line((40, 50), (960, 50), sw=2.2)
    d.text(40, 38, "house LAN (Ethernet)", "t-strong")

    # Pi 5
    d.line((240, 50), (240, 90))
    d.rect(60, 90, 360, 196)
    d.text(76, 114, "Raspberry Pi 5 — bench", "t-strong")
    rows = [
        ("Embedded-AI-Harness portal :8080", None),
        ("serial over network  rfc2217 :4001+", None),
        ("mosquitto :1884  (harness broker)", N),
        ("zigbee2mqtt  (test network, ch 25)", N),
        ("dfr-ota-server, test instance :8091", N),
        ("dfrharness runner · SQLite · alerts", N),
        ("boots from NVMe · wlan0 = WiFi test AP", "t-muted"),
    ]
    for i, (s, c) in enumerate(rows):
        if c == "t-muted":
            d.text(76, 140 + i * 20, s, "t-muted")
        else:
            d.text(76, 140 + i * 20, s, layer=c)
    d.text(248, 74, "eth0", "t-muted")

    # SLZB-06
    d.line((600, 50), (600, 90))
    d.rect(510, 90, 180, 74)
    d.text(524, 114, "SLZB-06 coordinator", "t-strong")
    d.text(524, 136, "CC2652P · Ethernet", "t-muted")
    d.text(524, 154, "powered by PoE", "t-muted")
    d.text(608, 74, "PoE", "t-muted")

    # external: HA + CI
    d.line((850, 50), (850, 90), dash="4 5")
    d.rect(730, 90, 240, 74, dash="4 5")
    d.text(744, 114, "Home Assistant (house)", "t-strong")
    d.text(744, 136, "bridge: harness/# only", "t-muted")
    d.text(744, 154, "dashboard + phone alerts", "t-muted")
    d.rect(730, 190, 240, 60, dash="4 5")
    d.text(744, 214, "GitHub Actions", "t-strong")
    d.text(744, 234, "builds what gets flashed", "t-muted")
    d.line((850, 164), (850, 190), dash="4 5")

    # USB hub
    d.line((240, 286), (240, 330))
    d.text(248, 314, "USB", "t-muted")
    d.rect(60, 330, 360, 54)
    d.text(76, 352, "powered USB hub", "t-strong")
    d.text(76, 372, "one port = one slot · label the ports", "t-muted")
    slots = [(110, "SLOT1"), (200, "SLOT2"), (300, "SLOT3"), (380, "SLOT4")]
    for x, s in slots:
        d.text(x, 400, s, "t-muted", "middle")

    # Fixture A + DUT A
    d.line((110, 384), (110, 450), cls=N)
    d.line((200, 384), (200, 450), cls=N)
    d.text(104, 432, "DUT USB", "t-muted", "end")
    d.text(206, 432, "Pico", "t-muted")
    d.rect(60, 450, 260, 110, cls=N)
    d.text(76, 474, "Fixture A", "t-strong", layer=N)
    d.text(76, 496, "Pico · relays ch1/ch2 · INA226 ×2", layer=N)
    d.text(76, 516, "ADS1115 · MCP4725 ×2 · sensors", layer=N)
    d.text(76, 540, "2×10 DUT connector", layer=N)

    # 24 V PSU into fixture
    d.rect(60, 600, 140, 44)
    d.text(76, 627, "24 V PSU", "t-strong")
    d.line((130, 600), (130, 560), cls="warn")
    d.text(138, 586, "24 V (blinds)", "t-muted")

    # fixture -> DUT
    d.rect(560, 450, 220, 110)
    d.text(576, 474, "DUT A", "t-strong")
    d.text(576, 496, "e.g. RollerBlinds unit", "t-muted")
    d.text(576, 516, "XIAO ESP32C6", "t-muted")
    d.line((320, 480), (560, 480), cls=N)
    d.text(440, 472, "USB, VBUS switched (relay ch1)", "t-muted", "middle")
    d.line((320, 510), (560, 510), cls=N, sw=3.2)
    d.text(440, 502, "adapter cable (2×10 ribbon)", "t-muted", "middle")
    d.line((320, 540), (560, 540), cls="warn")
    d.text(440, 532, "24 V (relay ch2)", "t-muted", "middle")

    # radio
    zig = [(600, 164)]
    y = 164
    for i in range(9):
        y += 30
        zig.append((620 if i % 2 == 0 else 640, y))
    zig.append((650, 450))
    d.line(*zig, dash="5 4")
    d.text(660, 300, "Zigbee, channel 25", "t-muted")
    d.text(660, 316, "test network only", "t-muted")

    # SLOT3/4 note
    d.line((300, 384), (300, 408), dash="3 4")
    d.line((380, 384), (380, 408), dash="3 4")
    d.text(290, 424, "SLOT3/4: fixture B + DUT B", "t-muted")
    d.text(290, 438, "(same pattern)", "t-muted")

    # legend
    d.line((600, 610), (640, 610), cls=N)
    d.text(650, 614, "added by this repo", "t-muted")
    d.line((600, 632), (640, 632), dash="4 5")
    d.text(650, 636, "external / wireless", "t-muted")
    return d, (1000, 670), (
        "Bench overview. A Raspberry Pi 5 on the house LAN runs the Embedded-AI-Harness "
        "portal plus the harness's own mosquitto, zigbee2mqtt, test OTA server and runner. "
        "An SLZB-06 coordinator joins the LAN over PoE. A powered USB hub gives one slot per "
        "board: each device under test has a fixture Pico in one slot and its own USB, "
        "switched by the fixture, in another. The fixture connects to the device by a "
        "2x10 ribbon and passes its 24 V supply. Home Assistant receives harness status "
        "over an MQTT bridge."
    )


def fixture_power():
    d = D()
    N = "new"
    # fixture boundary
    d.rect(175, 40, 605, 340, cls=N, dash="4 5", sw=1)
    d.text(186, 60, "fixture", "t-muted")

    # hub port
    d.rect(30, 62, 120, 94)
    d.text(90, 54, "hub port (DUT slot)", "t-strong", "middle")
    d.text(142, 84, "D+/D−", anchor="end")
    d.text(142, 104, "GND", anchor="end")
    d.text(142, 139, "VBUS", anchor="end")

    # DUT USB
    d.rect(800, 62, 170, 94)
    d.text(885, 54, "DUT (USB-C)", "t-strong", "middle")
    d.text(810, 84, "D+/D−")
    d.text(810, 104, "GND")
    d.text(810, 139, "VBUS")

    # data + gnd straight through
    d.line((150, 78), (800, 78))
    d.line((150, 82), (800, 82))
    d.text(560, 72, "D+ / D− straight through, short and twisted", "t-muted", "middle")
    d.line((150, 100), (800, 100))
    d.dot(720, 100)
    d.gnd(720, 100)
    d.text(732, 122, "GND", "t-muted")

    # VBUS -> INA1 -> relay1 -> DUT
    d.line((150, 135), (230, 135))
    d.rect(230, 118, 120, 46, cls=N)
    d.text(290, 136, "INA226 #1", "t-strong", "middle", layer=N)
    d.text(290, 154, "0x40 · 0.1 Ω", anchor="middle", layer=N)
    d.text(236, 176, "VIN+", "t-muted")
    d.text(344, 176, "VIN−", "t-muted", "end")
    d.line((350, 135), (470, 135))
    d.relay(470, 135, "relay ch1", cls=N)
    d.line((540, 135), (800, 135))
    d.dot(640, 135)
    d.line((640, 135), (640, 170))
    d.text(648, 168, "→ IDC pin 1 (VSW)", "t-muted")

    # Pico + coils
    d.rect(200, 186, 120, 70, cls=N)
    d.text(212, 206, "Pico", "t-strong", layer=N)
    d.text(312, 214, "GP16", anchor="end", layer=N)
    d.text(312, 242, "GP17", anchor="end", layer=N)
    d.line((320, 210), (470, 210), cls=N)
    d.rect(470, 198, 70, 24, cls=N)
    d.text(505, 214, "coil 1", anchor="middle", layer=N)
    d.line((505, 198), (505, 142), cls=N, dash="3 3", sw=1)
    d.line((320, 238), (440, 238), (440, 258), (470, 258), cls=N)
    d.rect(470, 246, 70, 24, cls=N)
    d.text(505, 262, "coil 2", anchor="middle", layer=N)
    d.line((505, 270), (505, 291), cls=N, dash="3 3", sw=1)
    d.text(556, 214, "10 kΩ pull-down on each IN,", "t-muted")
    d.text(556, 230, "HIGH-trigger jumper,", "t-muted")
    d.text(556, 246, "coils from Pico VBUS (5 V)", "t-muted")

    # 24 V path
    d.rect(30, 280, 120, 80)
    d.text(90, 272, "24 V PSU", "t-strong", "middle")
    d.text(142, 304, "+", anchor="end")
    d.text(142, 344, "−", anchor="end")
    d.line((150, 300), (190, 300), cls="warn")
    d.fuse(190, 300, cls=N)
    d.text(215, 324, "2 A T", "t-muted", "middle")
    d.line((240, 300), (270, 300), cls="warn")
    d.rect(270, 283, 120, 46, cls=N)
    d.text(330, 301, "INA226 #2", "t-strong", "middle", layer=N)
    d.text(330, 319, "0x41 · 0.1 Ω", anchor="middle", layer=N)
    d.line((390, 300), (470, 300), cls="warn")
    d.relay(470, 300, "relay ch2", cls=N)
    d.line((540, 300), (800, 300), cls="warn")
    d.rect(800, 280, 170, 80)
    d.text(885, 272, "DUT 24 V in (blinds)", "t-strong", "middle")
    d.text(810, 304, "+24 V")
    d.text(810, 344, "GND")
    d.line((150, 340), (800, 340))
    d.dot(600, 340)
    d.gnd(600, 340)
    d.text(588, 362, "one-point join to fixture GND", "t-muted", "end")

    # notes
    notes = [
        "NC contacts: the DUT stays powered if the fixture resets. Energising a relay is what cuts power.",
        "Blinds power cut = ch1 + ch2 together; ch2 alone leaves the XIAO running on USB.",
        "24 V never goes through the ribbon: screw terminals on the fixture only.",
    ]
    for i, s in enumerate(notes):
        d.text(30, 410 + i * 20, s, "t-muted")
    return d, (1000, 470), (
        "Fixture power paths. The DUT's USB VBUS runs from the hub port through INA226 number 1 "
        "and the normally-closed contact of relay channel 1 to the DUT, with a branch to IDC "
        "pin 1. Data and ground pass straight through. The 24 volt supply runs through a 2 amp "
        "fuse, INA226 number 2 and the normally-closed contact of relay channel 2 to the DUT. "
        "Pico GP16 and GP17 drive the relay coils."
    )


IDC = [
    ("VSW", "GND"), ("SENSE_A", "SENSE_B"), ("CH1", "CH2"), ("CH3", "CH4"),
    ("CH5", "CH6"), ("CH7", "CH8"), ("CH9", "CH10 ADC"), ("CH11 ADC", "CH12 ADC"),
    ("AOUT1", "AOUT2"), ("GND", "GND"),
]
CH_IDC = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16}


def fixture_signals():
    d = D()
    N = "new"
    # Pico
    d.rect(300, 60, 180, 500, cls=N)
    d.text(390, 52, "Raspberry Pi Pico (RP2040)", "t-strong", "middle")
    # right side: channels
    ys = {}
    for i in range(1, 10):
        ys[i] = 100 + (i - 1) * 26
    for i, y in zip((10, 11, 12), (360, 386, 412)):
        ys[i] = y
    for ch, y in ys.items():
        gp = 5 + ch if ch <= 9 else 16 + ch
        d.text(472, y + 4, f"GP{gp}", anchor="end", layer=N)
        d.line((480, y), (540, y), cls=N)
        d.res_h(540, y, cls=N)
        d.line((584, y), (640, y), cls=N)
        d.text(648, y + 4, f"CH{ch} → IDC {CH_IDC[ch]}")
    d.rect(530, 84, 64, 344, cls=N, dash="3 4", sw=1)
    d.text(562, 442, "330 Ω + clamp", "t-muted", "middle")
    d.text(562, 456, "(detail below)", "t-muted", "middle")
    d.text(366, 206, "CH1–CH9:", "t-muted", "middle")
    d.text(366, 222, "one PIO", "t-muted", "middle")
    d.text(366, 238, "sampler", "t-muted", "middle")
    d.text(366, 382, "CH10–12:", "t-muted", "middle")
    d.text(366, 398, "ADC0–2", "t-muted", "middle")

    # left side: I2C bus
    d.text(308, 114, "GP4 SDA", layer=N)
    d.text(308, 140, "GP5 SCL", layer=N)
    d.line((300, 110), (250, 110), (250, 420))
    d.line((300, 136), (262, 136), (262, 420))
    d.text(244, 100, "I²C0", "t-muted", "end")
    mods = [
        ("INA226 #1  0x40", "DUT USB 5 V, V and I"),
        ("INA226 #2  0x41", "24 V main, V and I"),
        ("ADS1115  0x48", "A0/A1 ← ÷2 ← IDC 3/4"),
        ("MCP4725 #1  0x60/62", "VOUT → IDC 17 (AOUT1)"),
        ("MCP4725 #2  base+1", "VOUT → IDC 18 (AOUT2)"),
    ]
    for i, (t, s) in enumerate(mods):
        y = 166 + i * 52
        d.rect(30, y, 190, 44, cls=N)
        d.text(40, y + 18, t, "t-strong", layer=N)
        d.text(40, y + 35, s, "t-muted")
        d.line((220, y + 12), (250, y + 12))
        d.dot(250, y + 12)
        d.line((220, y + 26), (262, y + 26))
        d.dot(262, y + 26)
    d.text(40, 452, "ADS1115 A2 ← TEMT6000 (light)", "t-muted")

    # left side: misc pins
    misc = [
        (480, "GP15", "1-Wire → DS18B20, 4.7 kΩ to 3V3"),
        (504, "GP16", "→ relay IN1 (DUT USB VBUS)"),
        (528, "GP17", "→ relay IN2 (24 V main)"),
        (552, "GP18", "← INA226 ALERT, wired-OR"),
    ]
    for y, gp, s in misc:
        d.text(308, y + 4, gp, layer=N)
        d.line((300, y), (40, y))
        d.text(46, y - 5, s, "t-muted")
    d.text(390, 590, "3V3(OUT) → all modules · VBUS → relay coils, A3144", "t-muted", "middle")

    # IDC header grid
    gx, gy, cw, rh = 772, 96, 104, 26
    d.text(gx + cw, 56, "DUT connector, 2×10 IDC", "t-strong", "middle")
    d.text(gx + cw, 72, "fixture side, shrouded", "t-muted", "middle")
    d.rect(gx - 8, gy - 8, cw * 2 + 16, rh * 10 + 16)
    d.rect(gx - 14, gy + rh * 4, 6, rh * 2, rx=1)  # key slot
    for r, (a, b) in enumerate(IDC):
        y = gy + r * rh
        for col, name in enumerate((a, b)):
            pin = r * 2 + col + 1
            x = gx + col * cw
            cls = N if name.startswith(("CH", "AOUT", "SENSE", "VSW")) else None
            d.rect(x + 2, y + 2, cw - 4, rh - 4, cls=cls, rx=2, sw=1)
            d.text(x + 10, y + 18, f"{pin:>2} {name}", layer=cls)
    d.text(gx + cw, gy + rh * 10 + 26, "pin 1 top-left · ≤ 30 cm", "t-muted", "middle")

    # channel protection detail
    bx, by = 300, 676
    d.text(bx, 622, "Every channel, at the IDC header:", "t-strong")
    d.text(bx + 40, by + 4, "GPx", anchor="end", layer=N)
    d.line((bx + 46, by), (bx + 100, by), cls=N)
    d.res_h(bx + 100, by, w=60, cls=N)
    d.text(bx + 130, by - 14, "330 Ω", anchor="middle", layer=N)
    d.line((bx + 160, by), (bx + 340, by), cls=N)
    d.dot(bx + 240, by, cls=N)
    d.diode_up(bx + 240, by, by - 40, cls=N)
    d.text(bx + 240, by - 46, "3V3", anchor="middle")
    d.diode_up(bx + 240, by + 40, by, cls=N)
    d.gnd(bx + 240, by + 40, cls=N)
    d.text(bx + 260, by - 22, "BAT54S", layer=N)
    d.text(bx + 348, by + 4, "IDC pin")
    d.text(bx, by + 84, "330 Ω limits a fight to ≈10 mA; the clamp holds the pin to −0.3…3.6 V.", "t-muted")
    return d, (1000, 780), (
        "Fixture signal wiring. Pico GP6 to GP14 are channels 1 to 9 and GP26 to GP28 are "
        "ADC-capable channels 10 to 12; each passes a 330 ohm resistor and a BAT54S clamp to "
        "its IDC pin. GP4 and GP5 form the I2C bus to two INA226s, an ADS1115 and two "
        "MCP4725 DACs. GP15 is 1-Wire, GP16 and GP17 drive the relays, GP18 takes the INA226 "
        "alert. The 2x10 IDC pinout is shown on the right."
    )


def blinds_adapter():
    d = D()
    N = "new"
    # connector column
    d.rect(40, 60, 190, 490, cls=N)
    d.text(135, 52, "fixture DUT connector", "t-strong", "middle")
    rows = [
        (100, "5  CH1  count"), (130, "6  CH2  capture"), (160, "7  CH3  capture"),
        (215, "8  CH4  capture"), (265, "9  CH5  capture"),
        (325, "14 CH10 drive+ADC"), (355, "15 CH11 drive+ADC"), (385, "16 CH12 drive+ADC"),
        (480, " 3 SENSE_A"), (505, " 4 SENSE_B"), (530, " 2/19/20 GND"),
    ]
    for y, s in rows:
        d.text(50, y + 4, s, layer=N)

    # TMC2209
    d.rect(620, 70, 170, 110)
    d.text(705, 62, "TMC2209 V1.3 (unit)", "t-strong", "middle")
    for y, s in ((100, "STEP  ← XIAO D8"), (130, "DIR   ← XIAO D7"), (160, "EN̅    ← XIAO D9")):
        d.line((230, y), (620, y), cls=N)
        d.dot(620, y, cls=N, r=3.5)
        d.text(630, y + 4, s)
    d.text(612, 92, "IC clamp", "t-muted", "end")

    # LED
    d.line((230, 215), (620, 215), cls=N)
    d.dot(620, 215, cls=N, r=3.5)
    d.rect(620, 198, 170, 34)
    d.text(630, 219, "D2 → 150 Ω → LED")
    d.text(612, 207, "clamp, D2 side", "t-muted", "end")
    d.text(800, 219, "+ TEMT6000 over the LED", "t-muted")

    # Hall
    d.line((230, 265), (620, 265), cls=N)
    d.rect(620, 246, 170, 40, cls=N)
    d.text(630, 262, "A3144 hall (rig only)", layer=N)
    d.text(630, 278, "Open reference mark", "t-muted")
    d.text(800, 262, "5 V supply, OC output", "t-muted")
    d.text(800, 278, "pull-up 10 kΩ to 3V3", "t-muted")

    # keypad Y
    d.rect(560, 305, 110, 100, cls=N)
    d.text(615, 297, "Y-adapter", "t-strong", "middle", layer=N)
    for y, k in ((325, "Fn"), (355, "Up"), (385, "Down")):
        d.line((230, y), (560, y), cls=N)
        d.line((670, y), (860, y))
        d.text(690, y - 5, k, "t-muted")
    d.rect(860, 305, 110, 100)
    d.text(915, 350, "membrane", "t-strong", "middle")
    d.text(915, 368, "keypad", "t-strong", "middle")
    d.line((615, 405), (615, 432), (700, 432))
    d.text(622, 424, "×3", "t-muted")
    d.rect(700, 414, 270, 36)
    d.text(710, 436, "unit input: 150 Ω + RC → D3/D4/D5")
    d.text(395, 412, "joins on the connector side, before the unit's RC", "t-muted", "middle")

    # rails
    d.rect(700, 470, 270, 80)
    d.text(960, 490, "XIAO ESP32C6", "t-strong", "end")
    d.line((230, 480), (680, 480), (680, 492), (700, 492), cls=N)
    d.text(710, 496, "5V (after 1N5822)")
    d.line((230, 505), (665, 505), (665, 514), (700, 514), cls=N)
    d.text(710, 518, "3V3")
    d.line((230, 530), (650, 530), (650, 536), (700, 536))
    d.text(710, 540, "GND / keypad common", "t-muted")

    d.text(40, 590, "USB (relay ch1) and 24 V (relay ch2) also pass through the fixture: see the power diagram.", "t-muted")
    return d, (1000, 610), (
        "RollerBlinds adapter. Fixture channels 1 to 3 clamp onto the TMC2209 STEP, DIR and "
        "enable pins; channel 4 taps the LED drive on the D2 side; channel 5 reads a hall "
        "sensor at the Open position. Channels 10 to 12 join the Fn, Up and Down key lines "
        "through a Y-adapter on the keypad connector, before the unit's RC front end. "
        "SENSE_A and SENSE_B read the XIAO 5 V and 3V3 pins."
    )


DIAGRAMS = [
    ("bench-overview", "Bench overview", bench_overview,
     "What sits on the bench and how it connects. Teal parts are what this repo adds on top of the upstream Embedded-AI-Harness bench."),
    ("fixture-power", "Fixture power paths", fixture_power,
     "Both supplies run through normally-closed relay contacts, so a fixture reset never cuts the DUT. Energising a relay is the power cut."),
    ("fixture-signals", "Fixture signals and DUT connector", fixture_signals,
     "Pico pin map, I²C modules, channel protection and the 2×10 connector every adapter plugs into."),
    ("blinds-adapter", "Adapter: DFR-RollerBlinds", blinds_adapter,
     "Where each fixture channel lands on a hand-built blinds unit. It taps the unit's own connectors and driver pins, so the joints are tested too."),
]

# ---------------------------------------------------------------- output

SVG_STYLE = """<style>
  svg { color: #34464c; font-family: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; }
  text { font-size: 12px; fill: currentColor; }
  .t-strong { font-family: "IBM Plex Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 600; }
  .t-muted { fill: #5b6b70; }
  .new { color: #0b7a84; }
  .new text { fill: #0b7a84; }
  .warn { color: #9a5b00; }
</style>
<rect width="100%" height="100%" fill="#ffffff"/>"""

PAGE_HEAD = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Harness Wiring, Rev 0</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {
  --bg: #f2f5f4; --panel: #ffffff; --ink: #17252b; --muted: #5b6b70;
  --rule: #d3dcdb; --wire: #34464c; --new: #0b7a84; --warn: #9a5b00;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0f1517; --panel: #162023; --ink: #dbe5e6; --muted: #93a4a8;
    --rule: #2b393d; --wire: #b4c3c6; --new: #52c6cf; --warn: #f0b458;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0f1517; --panel: #162023; --ink: #dbe5e6; --muted: #93a4a8;
  --rule: #2b393d; --wire: #b4c3c6; --new: #52c6cf; --warn: #f0b458;
}
body {
  background: var(--bg); color: var(--ink); margin: 0;
  font: 400 15px/1.6 "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  padding-inline: 16px; padding-block: 32px 64px;
}
.wrap { max-width: 1040px; margin: 0 auto; display: grid; gap: 40px; }
header { display: grid; gap: 8px; }
.eyebrow { font: 500 12px/1 "IBM Plex Mono", ui-monospace, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
h1, h2 { font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", system-ui, sans-serif; font-weight: 600; text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: 34px; } h2 { font-size: 22px; }
p { margin: 0; max-width: 68ch; }
.lede { color: var(--muted); font-size: 16px; }
section { display: grid; gap: 14px; }
code { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: .92em; }
figure { margin: 0; background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; padding: 16px; display: grid; gap: 12px; }
.scroll { overflow-x: auto; }
svg.dia { display: block; width: 100%; min-width: 760px; height: auto; color: var(--wire); }
svg.dia text { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 12px; fill: currentColor; }
svg.dia .t-strong { font-family: "IBM Plex Sans", system-ui, sans-serif; font-size: 13px; font-weight: 600; }
svg.dia .t-muted { fill: var(--muted); }
svg.dia .new { color: var(--new); }
svg.dia .new text { fill: var(--new); }
svg.dia .warn { color: var(--warn); }
figcaption { color: var(--muted); font-size: 14px; max-width: 80ch; }
</style>
<body>
<div class="wrap">
<header>
  <div class="eyebrow">DFR-test-harness · wiring</div>
  <h1>Harness Wiring, Rev 0</h1>
  <p class="lede">Bench, fixture power and signals, and the RollerBlinds adapter. Design stage: nothing here has been built yet. The text reference is <code>HARDWARE.md</code>; this page is generated by <code>docs/wiring/build.py</code>.</p>
</header>
"""


def main():
    page = [PAGE_HEAD]
    for name, title, fn, caption in DIAGRAMS:
        d, (w, h), aria = fn()
        body = d.svg_body()
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(aria)}">\n'
            f"{SVG_STYLE}\n{body}\n</svg>\n"
        )
        (OUT / f"{name}.svg").write_text(svg)
        page.append(
            f"<section>\n  <h2>{escape(title)}</h2>\n  <figure>\n    <div class=\"scroll\">\n"
            f'    <svg class="dia" viewBox="0 0 {w} {h}" role="img" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" aria-label="{escape(aria)}">\n{body}\n    </svg>\n'
            f"    </div>\n    <figcaption>{escape(caption)}</figcaption>\n  </figure>\n</section>\n"
        )
    page.append("</div>\n</body>\n</html>\n")
    (OUT / "wiring-diagram.html").write_text("".join(page))
    print("wrote", ", ".join(n for n, *_ in DIAGRAMS), "+ wiring-diagram.html")


if __name__ == "__main__":
    main()
