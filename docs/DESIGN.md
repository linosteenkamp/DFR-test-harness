# DFR Test Harness — Design

Status: **draft v0.1** (2026-10-11) · Owner: Lino Steenkamp

A hardware-in-the-loop (HIL) test harness for the DFR family of ESP32-C6
Zigbee devices (RollerBlinds, DoorSensor, MoistureTracker, and whatever comes
next). It flashes real boards, drives their inputs, watches their outputs and
radio traffic, and runs everything from a 30-second smoke test up to a
multi-week soak, with every project plugged in through a small per-project
profile.

The bench layer is the open-source
[SensorsIot/Embedded-AI-Harness](https://github.com/SensorsIot/Embedded-AI-Harness)
(Andreas Spiess, *"This AI Doesn't Just Write Code — It Tests Real
Hardware!"*). This repo adds what the DFR projects need on top of it: Zigbee
and MQTT, a fast signal monitor, wiring checks for hand-built units, noise and
phantom-press hunting, long soak runs, and per-project configuration.

Hardware to buy: [HARDWARE-SHOPPING.md](HARDWARE-SHOPPING.md).

---

## 1. Goals

| # | Goal | Why |
|---|------|-----|
| G1 | **Catch phantom inputs and measure noise margin** on input lines (keypad, contacts) while motors, bucks and radios are running | RollerBlinds has had coupled glitches on the keypad harness run the blind end to end, and the C6 glitch filter latching a released key "pressed" for 18 s (see `DFR-RollerBlinds/src/keypad.c`, `HARDWARE.md`) |
| G2 | **Soak for days or weeks** with randomised, realistic use, and catch the rare failure with enough context to fix it | Robustness problems show up at 1-in-10 000, not 1-in-30 |
| G3 | **Verify the wiring of every hand-built unit** before it's installed: every pin, every passive that matters, power rails, LED polarity | Units are built and soldered by hand; `tools/pinwalk` currently needs a person with a multimeter |
| G4 | **Track general health**: joins, re-joins, reboots, heap, link quality, OTA | One view of "is this unit healthy" over time |
| G5 | **Use Zigbee and MQTT heavily**, through zigbee2mqtt, exactly as production does | Every DFR device is a Zigbee device managed through z2m |
| G6 | **Switch between projects cheaply.** A new project should take a profile file, an adapter cable and its own tests, nothing else | Several current projects, more on the way |
| G7 | **Qualify `esp-zb-common` releases** against real hardware and every consuming project before anyone bumps their pin | The shared library is a single point of failure for the whole family |
| G8 | **Let Claude drive it.** The loop is code → build → flash → test → fix, with no human in the middle | The point of the Embedded-AI-Harness approach |

Non-goals (for now): RF compliance or range testing, production-line
throughput, and any testing that needs the device installed on a real blind,
door or plant pot.

---

## 2. System overview

```
                         LAN
  ┌──────────────────────┬───────────────────────────┬─────────────────────┐
  │                      │                           │                     │
  │  Dev machine /       │  Raspberry Pi 5 ("bench") │  SLZB-06 Zigbee     │
  │  Claude Code         │  ─────────────────────────│  coordinator        │
  │  (GitHub Actions     │  bench portal  :8080      │  (Ethernet, PoE)    │
  │   builds firmware)   │  mosquitto     :1884  ◄───┼── zigbee2mqtt uses  │
  │                      │  zigbee2mqtt   :8099 UI ──┼──► it over TCP      │
  │                      │  dfr-ota (test):8091      │                     │
  │                      │  dfrharness runner        │                     │
  │                      │  SQLite + HA status pub   │                     │
  └──────────────────────┴──────────┬────────────────┴─────────────────────┘
                                    │ USB hub (one port = one "slot")
             ┌──────────────────────┼────────────────────────┐
             │ SLOT1                │ SLOT2                  │ SLOT3 …
        DUT (XIAO C6)          Fixture Pico           DUT (FireBeetle C6)
             │                       │
             └── adapter cable ──────┤ 2×10 DUT connector
                                     ├── relay: DUT power cut
                                     ├── INA226 ×2: DUT USB 5 V and 24 V V/I
                                     ├── ADS1115: rail sense
                                     ├── MCP4725 ×2: analog stimulus
                                     └── light / hall / temp sensors
```

The **DUT** is the device under test (one DFR board). Each DUT has a
**fixture**: a Pico plus support parts that drives its inputs and watches its
outputs. The DUT and its fixture each sit in a bench **slot**. The units under
test are on their own **test Zigbee network**, separate from the house.

### 2.1 Repositories and responsibilities

| Repo | Holds |
|------|-------|
| **DFR-test-harness** (this) | Pi stack (Docker Compose), the `dfrharness` Python package and pytest plugin, the shared test suites, Pico fixture firmware, fixture hardware design, this document |
| **esp-zb-common** | Firmware side of the harness: `@H` structured log lines, the `zb_test` console, `key_filter` (moved from RollerBlinds), `END_DEVICE` role. Also gets its own `harness/` profile using `examples/minimal_router` |
| **DFR-\<project\>** | `harness/harness.yaml` (profile), `harness/tests/` (project tests and soak scenarios), and an adapter-cable drawing |
| **dfr-ota-server** | Reused unchanged. A second, test-only instance on the bench serves CI/pre-release images to the test network |
| **SensorsIot/Embedded-AI-Harness** | Upstream bench (portal, slots, RFC2217 serial, flashing, recovery, GDB, WiFi AP, BLE, MCP tools, Claude skills). Installed on the Pi, not forked unless we need to |

---

## 3. Bench Pi software stack

### 3.1 Components

| Service | How it runs | Port | Notes |
|---------|-------------|------|-------|
| Embedded-AI-Harness portal | systemd (its own `install.sh`) | 8080, 4001+ (RFC2217), 3333+ (GDB) | Unmodified upstream |
| mosquitto (harness broker) | Docker Compose | **1884** | Permanent, password auth. *Not* the bench's own broker on 1883, which the bench starts, stops and resets as part of WiFi tests |
| zigbee2mqtt | Docker Compose | 8099 (UI) | Test network; external converters mounted from each project repo |
| dfr-ota-server (test instance) | Docker Compose or systemd | 8091 | `repos.conf` points at test/pre-release artefacts |
| dfrharness runner | systemd (`dfrharness-soak.service`) and on demand (`dfrh run …`) | — | Writes SQLite and publishes status to MQTT |
| Home Assistant link | optional MQTT bridge from 1884 to the house broker | — | Bridges `harness/#` only, never `zigbee2mqtt/#` |

`compose/` in this repo will hold `docker-compose.yml`, `mosquitto.conf`,
the z2m `configuration.yaml` template, and the test dfr-ota config.

### 3.2 Constraints from the upstream bench

* **USB serial devices are claimed as slots.** The bench's udev rule
  (`pi/udev/99-rfc2217-hotplug.rules`) claims every `ttyUSB*`/`ttyACM*`.
  A USB Zigbee dongle would be taken over, and so would the SLZB-06's USB
  port, because it also presents a serial device. **Use the SLZB-06 over Ethernet** and power it from PoE or a plain USB charger,
  never from the Pi or the slot hub. If a USB coordinator is ever used, add a
  udev exclusion by `ID_PATH` before plugging it in.
* **One writing serial client per slot.** The runner takes the slot lease
  (`/api/slot/...`) for the duration of a test and releases it on exit. A
  soak run holds a long lease and renews it.
* **No authentication on the bench API.** Keep the Pi on a trusted LAN or
  VLAN. Use Tailscale for remote access, never port forwarding.
* **2.4 GHz coexistence.** The bench's WiFi test AP and Zigbee share the
  band. Pin z2m to **Zigbee channel 25** (≈2475 MHz), and keep the AP and the
  house WiFi on channel 1 or 6.

### 3.3 Storage and resilience

* Boot from **NVMe** (M.2 HAT+), not SD. Weeks of logs and SQLite writes wear SD cards out.
* journald and container logs are size-capped. Per-run artefacts (serial
  logs, captures) rotate by age, but **failure artefacts are kept** until
  someone acknowledges them.
* Every service is set to restart automatically. The runner must survive a Pi reboot mid-soak: it
  resumes from the last checkpoint in SQLite.

### 3.4 Zigbee test network

* Separate PAN ID, extended PAN ID and network key from the house network,
  stored in z2m `configuration.yaml` in `compose/` (key generated at install,
  not committed).
* External converters: each project's `z2m/*.js` is mounted read-only from
  its repo checkout, so tests always use the converter from the commit under
  test.
* OTA: `ota.zigbee_ota_override_index_location` points at the test
  dfr-ota-server (`http://127.0.0.1:8091/index.json`).
* Device naming: friendly names are `<project>/<unit-id>`, for example
  `rollerblinds/u007`, and are set by the runner after pairing.

---

## 4. Fixture hardware

One fixture per DUT. It plugs into a bench slot like any other board.

### 4.1 Fixture Pico (RP2040)

Twelve generic **channels** (CH1–CH12). Each is configured per run as one
of the following modes:

| Mode | Use | Implementation |
|------|-----|----------------|
| `capture` | Time-stamp every edge (µs) | PIO edge sampler → DMA ring |
| `count` | Pulse counter (STEP), with optional direction from another channel | PIO counter |
| `open_drain` | Simulate a button or contact to GND: drive low or release | GPIO output-low / input |
| `push_pull` | Drive a logic level | GPIO |
| `adc` | Sample voltage: min/max/histogram, or streamed | RP2040 ADC (CH10–CH12 only = GPIO26–28) |
| `glitch_watch` | Report any edge outside an "expected" window, with a pre/post-trigger capture of all channels | `capture` plus a trigger |

Every channel has a **330 Ω series resistor** and a **3.3 V clamp** on the
fixture board. DUT signals are 3.3 V logic only. Anything else (24 V, the 5 V
rail) goes through the ADS1115 with dividers, never directly to the Pico.

The I²C bus on the fixture (Pico GP4/GP5) carries two INA226s, the ADS1115
and two MCP4725 DACs; the DS18B20 is on 1-Wire (GP15). The full pin map,
addresses and wiring are in [HARDWARE.md](../HARDWARE.md).

### 4.2 DUT connector (2×10 IDC, 2.54 mm)

Project-agnostic. Each project gets an **adapter cable or board** that
routes its DUT pins onto this connector.

| Pin | Signal | Pin | Signal |
|-----|--------|-----|--------|
| 1 | `VSW` switched DUT 5 V (same rail as the DUT's USB VBUS, through relay ch1 NC; ≤1 A) | 2 | GND |
| 3 | `SENSE_A` (ADS1115 A0, ÷2: up to 6.6 V) | 4 | `SENSE_B` (ADS1115 A1, ÷2) |
| 5 | CH1 | 6 | CH2 |
| 7 | CH3 | 8 | CH4 |
| 9 | CH5 | 10 | CH6 |
| 11 | CH7 | 12 | CH8 |
| 13 | CH9 | 14 | CH10 (ADC-capable) |
| 15 | CH11 (ADC-capable) | 16 | CH12 (ADC-capable) |
| 17 | `AOUT1` (MCP4725 #1) | 18 | `AOUT2` (MCP4725 #2) |
| 19 | GND | 20 | GND |

**High-current and high-voltage paths do not go through the ribbon.** The
blinds' 24 V supply passes through screw terminals on the fixture: INA226
shunt, then relay channel 2, then the unit. That lets the fixture measure
motor-side current and cut 24 V independently of the 5 V logic supply.

### 4.3 Optional sensors (per project, on flying leads)

| Sensor | Purpose |
|--------|---------|
| TEMT6000 light sensor taped over the LED | Confirms the LED actually lights. Catches reversed polarity, which a voltage check at the GPIO cannot |
| A3144 hall sensor and magnet at a mechanical reference (blinds: Open position) | Detects open-loop position drift over long soaks |
| DS18B20 on the stepper driver or buck | Temperature trend during soak |
| Nordic PPK2 (in series with the DUT supply) | µA-level sleep-current profiling for battery projects (MoistureTracker) |
| USB logic analyzer (sigrok) | Occasional deep dives on one glitch at 24 MHz. The Pico handles continuous monitoring |

### 4.4 Pico firmware protocol (USB CDC, line-based JSON)

```
> {"cmd":"cfg","ch":4,"mode":"count","dir_ch":5}
> {"cmd":"cfg","ch":10,"mode":"adc","rate":50000,"stats":true}
> {"cmd":"set","ch":1,"v":0}            # press (open-drain low)
> {"cmd":"set","ch":1,"v":"z"}          # release
> {"cmd":"watch","ch":[10,11,12],"expect":"idle","pre_ms":50,"post_ms":50}
< {"ev":"edge","ch":1,"lvl":0,"t_us":123456789}
< {"ev":"count","ch":4,"n":38400,"dir":1}
< {"ev":"adc","ch":10,"min_mv":2710,"max_mv":3302,"n":500000}
< {"ev":"glitch","ch":11,"t_us":...,"width_us":3,"capture":"cap-000123"}
```

The timestamps are the Pico's own µs clock. The runner records the offset
to the Pi clock at session start and every minute, so the Pico's events line
up with the serial log and MQTT.

---

## 5. Firmware side (esp-zb-common)

All of this goes in the library, so every project gets it by consuming
`esp-zb-common`. It is compiled in only when `DFR_TEST_HOOKS` is defined,
which the projects' existing `*_zigbee_test` PlatformIO envs set. Release
builds are unchanged.

### 5.1 `@H` structured log lines

One line per event, on the normal console:

```
@H <ms_since_boot> <topic> key=value key=value ...
```

| Emitted by | Lines |
|------------|-------|
| `zb_core` | `zb state=steering`, `zb state=joined addr=0x1a2b ch=25`, `zb state=left type=0`, `zb steer_retry ms=8000`, `zb factory_reset` |
| `ota_client` | `ota state=query`, `ota state=download pct=40`, `ota state=verify_pending ver=0x00020500`, `ota state=valid`, `ota state=rollback`, `ota stall` |
| `zb_test` | `boot reason=POWERON fw=2.5.0 lib=0.3.0 heap_min=123456`, periodic `health heap=… heap_min=… uptime_s=…` |
| app (via `zb_test_emit()`) | blinds: `key id=up kind=tap`, `led base=CAL_MARK1`, `led flash=ACK`, `move from=… to=…`, `move_done steps=…`; door: `contact state=open`; moisture: `sample soil_mv=… pct=…` |

The format is space-separated `key=value`, values without spaces, parsed by one regex
in `dfrharness`. A line that starts `@H` is never chatty and never logged
in a loop.

### 5.2 `zb_test` console

A small line console on the USB-Serial-JTAG console, `_test` builds only:

| Command | Effect |
|---------|--------|
| `status` | fw/lib version, join state, short addr, channel, uptime, heap |
| `trace` | Dump the app's trace ring (apps register a dump callback; blinds already has one) |
| `leave` / `factory_reset` | Force a Zigbee leave / factory reset |
| `reboot` | Software restart |
| `pinwalk <gpio...>` | Toggle the listed GPIOs one by one (wiring check, §7.1). Replaces `tools/pinwalk` for fixture-based checks |
| `pinread <gpio...>` | Report input levels (wiring check, input direction) |
| `app <…>` | Forwarded to an app-registered handler (project-specific commands) |

### 5.3 Library changes this design implies

| Change | Why | Version |
|--------|-----|---------|
| `@H` emitters in `zb_core` and `ota_client`, plus the `zb_test` module | §5.1, §5.2 | 0.3.0 |
| Move RollerBlinds' `key_filter` (integrator with swallowed/traverse telemetry) into the library, alongside `debounce` | Same noise immunity and the same near-miss telemetry for every input-driven device. The phantom suite (§7.4) can measure the benefit | 0.3.0 |
| `ZB_CORE_ROLE_END_DEVICE` | MoistureTracker retrofit. Sleepy behaviour is the hardest thing to test by hand, and the harness covers it (§7.3) | 0.4.0 |
| Migrate DoorSensor from its own `zb_router.c`/`ota_client.c` copies to the library | One code path. Run the harness before and after: identical results mean a safe migration | after 0.3.0 |

---

## 6. Per-project profile

Each project repo has `harness/harness.yaml`:

```yaml
# DFR-RollerBlinds/harness/harness.yaml
project: rollerblinds
board: seeed_xiao_esp32c6
pio_env: seeed_xiao_esp32c6_zigbee_test     # defines DFR_TEST_HOOKS
zigbee:
  role: router
  model: DFR-RollerBlinds
  converter: z2m/dfr_roller_blinds.js
  expose: [position, state, motor_reversed, calibrated, travel_time]
power:
  logic: { via: vsw }                       # 5 V via the ribbon, relay ch1
  main:  { via: terminals, volts: 24, relay: 2, ina226: 0x40 }
signals:                                    # DUT gpio → fixture channel
  key_fn:   { gpio: 21, ch: 10, mode: open_drain, active: low, adc: true }
  key_up:   { gpio: 22, ch: 11, mode: open_drain, active: low, adc: true }
  key_down: { gpio: 23, ch: 12, mode: open_drain, active: low, adc: true }
  step:     { gpio: 19, ch: 1,  mode: count, dir: dir }
  dir:      { gpio: 17, ch: 2,  mode: capture }
  en:       { gpio: 20, ch: 3,  mode: capture, active: low }
  led:      { gpio: 2,  ch: 4,  mode: capture }
sensors:
  led_light: { type: temt6000, adc: ads1115.a2 }
  home:      { type: hall, ch: 5 }
  driver_t:  { type: ds18b20 }
wiring:                                     # §7.1 expectations
  passives:
    key_rc: { signals: [key_fn, key_up, key_down], rise_us: [300, 800] }  # 4.7k × 100n ≈ 470 µs
  rails:
    v5_after_diode: { sense: SENSE_A, mv: [4400, 4800] }
timing:
  tap_ms: 150
  hold_ms: 1000
  fn_long_ms: 3500
soak:
  scenarios: harness/soak.py
```

```yaml
# DFR-DoorSensor/harness/harness.yaml (abridged)
project: doorsensor
board: dfrobot_firebeetle2_esp32c6
pio_env: dfrobot_firebeetle2_esp32c6_zigbee_test
zigbee: { role: router, model: DFR-DoorSensor, converter: z2m/dfr_door_sensor.js }
signals:
  contact: { gpio: 5, ch: 10, mode: open_drain, adc: true }
```

```yaml
# DFR-MoistureTracker/harness/harness.yaml (abridged)
project: moisture
board: dfrobot_firebeetle2_esp32c6
pio_env: dfrobot_firebeetle2_esp32c6_zigbee_test
zigbee: { role: sleepy_end_device, model: DFR-SoilSensor, converter: z2m/dfr_soil_moisture.js }
signals:
  soil:    { ch: AOUT1, mode: analog_out, range_mv: [0, 3000] }
  battery: { ch: AOUT2, mode: analog_out, range_mv: [3000, 4200], divider: 2 }  # match board divider
power:
  logic: { via: ppk2 }                       # µA profiling
```

The profile is validated against a JSON schema shipped in `dfrharness`. A
profile that maps two signals to one channel, or an `adc: true` signal to a
non-ADC channel, is rejected before anything is powered.

---

## 7. Test catalogue

Every test is pytest, collected from the shared suites in this repo plus the
project's `harness/tests/`. Markers select the tier: `smoke` (< 1 min),
`full` (< 30 min), `noise` (hours), `soak` (days).

### 7.1 Commissioning: wiring check of a hand-built unit (G3)

Run once per new unit, through the unit's real connectors, using the
adapter cable. It produces a stored pass/fail report keyed by unit ID.

| Check | Method | Catches |
|-------|--------|---------|
| Rails | ADS1115: 5 V after the diode, 3V3. INA226: 24 V | Missing or reversed Schottky (HARDWARE.md §Power chain), dead buck |
| Outputs (STEP, DIR, EN, LED, …) | `zb_test pinwalk`: each GPIO high in turn, fixture captures all channels | Open joints, swapped wires, shorts to a neighbour (two channels move together) |
| Inputs (keys, contacts) | Fixture pulls each line low in turn, `zb_test pinread` | Swapped/open lines, missing pull-up (line idles low) |
| Input RC front-end | Release a line and measure rise time on the fixture ADC/capture: about 470 µs = 4.7 k with 100 nF fitted; about 4 ms = internal pull-up only; under 50 µs = cap missing | Missing or wrong-value RC parts on a keypad line |
| LED polarity | Firmware sets LED on; TEMT6000 must see light | Reversed LED |
| Driver and motor (blinds) | Short move: STEP count = commanded; 24 V current rises when EN is low, falls when it goes high; hall sees the magnet | EN not wired, VCC_IO missing (no motion, no current change), open coil, wildly wrong Vref |
| Radio | Join the test network, interview, LQI above a threshold at 1 m | Antenna/RF switch (blinds `PIN_RF_SW_EN`, `PIN_RF_ANT`), U.FL not seated |

### 7.2 Shared Zigbee and OTA suite (G4, G5, G7)

Run against every project and against `esp-zb-common`'s `minimal_router`.

* **Join and interview:** model ID, firmware version and the converter's
  exposes appear in z2m.
* **Factory reset** (console and, where defined, button gesture), then
  re-pair.
* **Coordinator outage:** stop z2m or power-cycle the SLZB-06, then check
  `@H zb steer_retry` back-off and automatic re-join (the rejoin-recovery
  design in RollerBlinds).
* **Removal:** z2m removes the device, which goes to `zb state=left` and
  steers again.
* **OTA upgrade:** a version-bumped image (built with `esp-zb-common`'s
  `make_ota_image.py`) goes to the test dfr-ota-server. z2m update, then
  `verify_pending`, then `valid`, and the new version is reported.
* **OTA rollback:** an image built to fail its self-check rolls back and
  reports the old version.
* **OTA stall:** cut the coordinator mid-download, then check the stall
  watchdog and recovery.
* **Availability:** `last_seen` and LQI recorded per minute in every long run.

### 7.3 Project functional tests

The project's own `harness/tests/`. For example:

* **RollerBlinds:**
  - tap and hold gestures,
  - calibration flow (LED via `@H led` and the light sensor),
  - go-to-% over MQTT (step count matches `position` × span),
  - motor reversed,
  - travel time,
  - power cut mid-move, then Position Unknown, then Re-home.
* **DoorSensor:** contact open/close maps to the IAS Zone status in z2m,
  including fast chatter.
* **MoistureTracker:**
  - DAC sweeps the soil voltage and the reported % follows the calibration,
  - DAC lowers the battery voltage and low-battery behaviour kicks in,
  - sleep current per cycle from the PPK2,
  - sleepy OTA.

### 7.4 Noise and phantom suite (G1)

The harness always knows when it commanded an input. **Any input event
(fixture edge or `@H key`/`contact` line) outside a commanded window is a
phantom**, and the run records it with a full capture.

| Test | Procedure | Pass |
|------|-----------|------|
| Quiet-input run | Motor (or other noise source) runs continuously in random moves for N hours; no inputs commanded | 0 phantom events, 0 fixture glitches deeper than threshold |
| Margin trend | Same run; record the ADC min on each key line and the firmware's `TRC_KEY_SWALLOWED` counts | Report trend; alert when the margin shrinks run over run |
| Release honoured | Hold-to-jog, release, measure release→last STEP; repeat 10 000× | Every stop < `HOLD_RELEASE_MAX_MS`; 0 runaway jogs |
| Commanded press honoured | Tap during motion; repeat | 0 swallowed real presses |
| Worst case | Keypad lead run alongside the motor cable at full length; vary travel time (step rate); run with and without the RC front-end on one line for A/B | Gives *numbers* for a hardware change (ferrite, shielded cable, RC values) instead of impressions |

When a phantom happens, the evidence bundle holds the fixture capture of all
channels ±50 ms around the event (STEP/EN activity shows whether it lines up
with motor or driver switching), the serial log window, a trace-ring dump,
and the DUT supply current from the INA226.

### 7.5 Soak (G2)

`dfrharness-soak.service` runs one or more DUTs indefinitely:

* **Scenario mix (per project, weighted random):**
  - blinds: go-to-% over MQTT, keypad taps and holds, open/close, idle
    periods, occasional recalibration, occasional power cut mid-move,
    occasional coordinator outage, occasional OTA up and back down;
  - door: contact flips at random intervals including chatter;
  - moisture: sweeps and sleep cycles.
* **Invariants, checked after every action:**
  - reported state matches the command and the fixture measurement (step
    count, contact level);
  - no phantom inputs;
  - no unexpected reboot (`@H boot` outside a planned power cut);
  - heap low-water mark not decreasing over a 24 h window;
  - device available in z2m;
  - blinds: hall sensor sees the magnet at every return to Open (drift
    check).
* **Duty cycle:** configurable. The motor and driver temperature from the
  DS18B20 caps the rate, so a soak doesn't cook the rig.
* **On a failure:** save the evidence bundle, publish an alert, then either
  continue (default for non-fatal faults) or pause the DUT (fatal: runaway,
  over-temperature, over-current).
* **Results:** cycles, failures by class, MTBF estimate, and the margin
  trends, per DUT, per firmware commit, per library version.

### 7.6 Library release qualification (G7)

Before tagging `esp-zb-common` vX.Y.Z:

1. Flash `examples/minimal_router` and run §7.2 plus an overnight join-stability soak.
2. For each consuming project, build with `override_path` pointing at the
   candidate and run its `full` tier.
3. Publish the pass/fail matrix (library version × project) as a check on the
   library PR.

---

## 8. dfrharness (Python package)

```
dfrharness/
  bench.py      # wraps upstream TestbenchDriver: slots, leases, flash, serial, reset
  dut.py        # one DUT: profile + slot + fixture + z2m name; @H parser; console
  fixture.py    # Pico protocol client; channel config from the profile
  power.py      # relays, INA226, PPK2
  z2m.py        # MQTT client to 1884: permit_join, rename, remove, set/get, OTA, availability
  ota.py        # build test images (make_ota_image.py), publish to the test dfr-ota
  profile.py    # load + schema-validate harness.yaml
  store.py      # SQLite: runs, events, failures, metrics, artefacts
  alerts.py     # MQTT harness/# status, HA discovery, ntfy push
  soak.py       # scheduler, scenario API, invariants, checkpoints, resume
  pytest_plugin.py   # fixtures: dut, fixture, z2m, power, evidence; markers; CLI options
  cli.py        # dfrh run | commission | soak | report | bench-status
```

Example test, as it would read in a project repo:

```python
@pytest.mark.full
def test_tap_up_runs_to_open(dut, z2m):
    dut.goto_pct(50)                                # over MQTT, waits for position
    with dut.expect_steps(direction="open", approx=dut.span * 0.5, tol=0.02):
        dut.tap("key_up")
    assert z2m.state(dut).position == 100
    dut.assert_no_phantoms()
```

Firmware under test always comes from CI artefacts (as the upstream method
requires), so the bytes flashed are the bytes in a traceable run. Local
builds are allowed for interactive debugging, and their results are marked
`local`.

---

## 9. Reporting and alerting

* **SQLite** (`/var/lib/dfrharness/harness.db`) with tables for runs, tests,
  events (one row per `@H` line, fixture event or MQTT message of interest),
  failures (each with an evidence bundle path), metrics (time series) and
  units (commissioning reports).
* **MQTT status** on 1884, `harness/<project>/<unit>/…`: state, cycles,
  phantoms, last failure, margin. Home Assistant MQTT discovery configs are
  published, so a dashboard and phone notifications come for free.
* **ntfy** push as a fallback when Home Assistant isn't reachable.
* `dfrh report --since 7d` gives a markdown summary per DUT, suitable for a
  PR comment or an issue.

---

## 10. Running several projects and DUTs

* **One DUT = one slot + one fixture (another slot) + one z2m friendly name.**
  The bench's slot identity is per USB port, so a fixture and its DUT are
  paired by port in `/etc/dfrharness/bench.yaml`.
* Several DUTs can soak at once, even of different projects. They share z2m
  and the broker, and each has its own lease and its own SQLite run.
* **Switching a slot to another project:** swap the adapter cable, then
  `dfrh assign SLOT2 doorsensor --unit d003`. The runner reads that
  project's profile at the requested ref and re-checks the wiring (§7.1
  smoke subset) before running anything else.
* **Adding a new project:**
  1. consume `esp-zb-common` (which brings the hooks);
  2. add `*_zigbee_test` with `-DDFR_TEST_HOOKS`;
  3. write `harness/harness.yaml`;
  4. make an adapter cable;
  5. write project tests.

  The shared suites run with no extra work.

---

## 11. Build order

| Phase | Deliverable | Exit criterion |
|-------|-------------|----------------|
| **0. Bench up** | Pi 5 + NVMe + upstream Embedded-AI-Harness installed; blinds DUT flashes and monitors via slot | `curl $BENCH:8080/api/devices` lists the XIAO; `pio run -t upload` via `rfc2217://` works |
| **1. Zigbee stack** | `compose/` with mosquitto:1884, z2m on the SLZB-06, test dfr-ota; blinds converter loaded | Blinds unit pairs on the test network; go-to-% from a script works |
| **2. Firmware hooks** | `esp-zb-common` 0.3.0: `@H`, `zb_test`, `key_filter`; blinds bumps its pin | `@H zb state=joined` and `@H key …` seen on the bench serial |
| **3. dfrharness core** | profile loader, bench/dut/z2m/store, pytest plugin, shared §7.2 smoke tests | `dfrh run rollerblinds --tier smoke` green on real hardware |
| **4. Fixture v1** | Pico firmware (capture/count/open_drain/adc), perfboard fixture, blinds adapter cable | Step counts and key presses driven from tests; LED via capture and light sensor |
| **5. Commissioning** | §7.1 wiring check for blinds | A deliberately mis-wired unit (swapped keys, missing cap, reversed LED) fails with the right reasons |
| **6. Noise and phantom** | §7.4 suite; glitch_watch capture bundles | Overnight quiet-input run with margin trend in the report |
| **7. Soak** | soak service, invariants, alerts, HA dashboard | 7-day blinds soak running unattended, failures with evidence |
| **8. More projects** | DoorSensor profile (before/after library migration), MoistureTracker (with `END_DEVICE`, PPK2) | Shared suites green on all three |
| **9. Library qualification** | §7.6 matrix as a CI check on `esp-zb-common` PRs | Matrix posted on a real library PR |
| **10. Fixture v2** | Proper PCB for the fixture (KiCad in `hardware/`) | — |

---

## 12. Risks and open questions

| Risk / question | Mitigation / next step |
|-----------------|------------------------|
| Phantoms on installed units come from real cable runs that the bench doesn't reproduce | Build the worst-case rig (§7.4) with production-length leads next to the motor cable, and keep a spare installed unit with the trace ring as field evidence |
| Upstream bench changes under us | Pin the Embedded-AI-Harness version on the Pi; upgrade on purpose |
| Sleepy end-device OTA and availability are slow, so tests take long | `soak` tier only; tune z2m availability timeouts per profile |
| Pico ADC (≈500 kS/s, 12-bit, noisy) may miss sub-µs spikes on key lines | The digital `glitch_watch` catches threshold crossings anyway; the logic analyzer or a scope for deep dives |
| 24 V and motor on the bench | Fuse the 24 V feed at the fixture; the INA226 over-current trip pauses the DUT; never route 24 V through the ribbon |
| PoE vs USB power for the SLZB-06 | PoE preferred. If USB-powered, use a separate charger so the bench never sees its serial port |
| What is `HOLD_RELEASE_MAX_MS`? | Derive from `key_filter` (60 ms full traverse) + deceleration ramp; confirm on the bench in phase 6 |
| MoistureTracker pin map and divider | Fill in its profile from `main.c` / `battery_monitor.c` in phase 8 |
