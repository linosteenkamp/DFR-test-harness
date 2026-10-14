# DFR-test-harness

Hardware-in-the-loop test harness for the DFR family of ESP32-C6 Zigbee
devices (RollerBlinds, DoorSensor, MoistureTracker, and future projects),
built on a Raspberry Pi bench running
[SensorsIot/Embedded-AI-Harness](https://github.com/SensorsIot/Embedded-AI-Harness),
plus zigbee2mqtt, MQTT, a Pico-based signal fixture, and per-project profiles.

- **[docs/DESIGN.md](docs/DESIGN.md)** — goals, architecture, fixture,
  firmware hooks (`esp-zb-common`), project profiles, test catalogue
  (wiring check, Zigbee/OTA, phantom-press/noise, soak), build order
- **[HARDWARE.md](HARDWARE.md)** — wiring reference: bench Pi, fixture
  Pico pin map, power chain and relays, DUT connector, per-project adapters,
  bring-up order, troubleshooting
- **[docs/HARDWARE-SHOPPING.md](docs/HARDWARE-SHOPPING.md)** — parts to
  source, with South African supplier links

Status: design stage — nothing to install yet.
