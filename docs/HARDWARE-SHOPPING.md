# Hardware shopping list (South Africa)

What to buy for the DFR test harness described in [DESIGN.md](DESIGN.md).

> **Prices and stock** were taken from supplier search listings on
> **2026-10-11** and are approximate (incl. VAT where stated). They change
> often. Check the live page before ordering. "—" means no price was found.
> The links were found through web search; open each one before buying to
> confirm it's the right part.

Suppliers used:
* [PiShop](https://www.pishop.co.za)
* [Micro Robotics](https://www.robotics.org.za)
* [Communica](https://www.communica.co.za)
* [DIYElectronics](https://www.diyelectronics.co.za)
* [Botshop](https://www.botshop.co.za)
* [GeeWiz](https://www.geewiz.co.za)
* [RS Components ZA](https://za.rs-online.com)
* [Takealot](https://www.takealot.com)

Priority:
**P1** = needed for phases 0–4 (bench, Zigbee, first tests).
**P2** = commissioning, noise and soak (phases 5–7).
**P3** = other projects and nice-to-have.

---

## 1. Bench computer (P1)

| Qty | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 | Raspberry Pi 5, 4 GB (8 GB if available, for more headroom) | Runs the bench, z2m, mosquitto, runner | [PiShop — Pi 5 4GB](https://www.pishop.co.za/store/raspberry-pi-5-model-b-4gb) | R2 145 (was out of stock) |
| 1 | Official 27 W USB-C PSU (EU plug, needs an SA adapter) | Pi 5 + NVMe + USB hub load | [PiShop — 27W PSU black](https://www.pishop.co.za/store/raspberry-pi-official-27w-usb-c-power-supply-black-51v-5a-psu-type-eufor-pi5) | — |
| 1 | Official Active Cooler | Weeks of continuous running | [PiShop — Active Cooler](https://www.pishop.co.za/store/raspberry-pi-5-active-cooler) | R100 |
| 1 | Raspberry Pi 256 GB SSD **kit** (M.2 HAT+ + SSD) | Boot from NVMe, not SD (log/DB wear) | [PiShop — 256GB SSD kit](https://www.pishop.co.za/store/raspberry-pi-256gb-ssd-kit) (or [HAT+](https://www.pishop.co.za/store/raspberry-pi-m2-hat--for-raspberry-pi-5) + [SSD](https://www.pishop.co.za/store/raspberry-pi-ssd---256gb) separately) | R850 kit |
| 1 | microSD card, 16–32 GB | First boot / rescue only | any | — |
| 1 | Case that fits Pi 5 + Active Cooler + M.2 HAT+ (or standoffs) | | [PiShop — Pi 5 cases](https://www.pishop.co.za/store/raspberry-pi-5-cases) | — |
| 1 | Powered USB hub, 4–7 ports, **with its own PSU**. Individual port switches are handy | One port = one bench slot (DUTs + fixtures). Rough budget is two slots per DUT | [Takealot — 7-port, individual switches](https://www.takealot.com/7-port-usb-hub-with-individual-power-switches-black/PLID95940283) · [Micro Robotics — Waveshare industrial 4-port](https://www.robotics.org.za/W20861) · [PiShop — USB hubs](https://www.pishop.co.za/store/usb-access) | — |
| 4+ | Short USB **data** cables (USB-C for XIAO/FireBeetle, micro-USB for Pico) | Charge-only cables are the #1 "device not detected" cause | any | — |
| 1 | Ethernet cable for the Pi | Bench stays on wired LAN; wlan0 is the bench's test AP | any | — |

## 2. Zigbee coordinator (P1)

| Qty | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 | **SMLIGHT SLZB-06 (CC2652P), PoE version** | Ethernet coordinator for z2m. Stays off the bench's USB hub, which would otherwise claim it as a slot | [GeeWiz — SLZB-06 PoE](https://www.geewiz.co.za/networking/283533-smlight-slzb-06-zigbee-30-to-ethernet-cc2652p-chip-poe-version.html) | R1 095 |
| (alt) | SLZB-06 non-PoE | Power from a **separate USB charger**, never the Pi or hub | [GeeWiz — SLZB-06 non-PoE](https://www.geewiz.co.za/networking/281691-smlight-slzb-06-zigbee-30-to-ethernet-cc2652p-chip-non-poe-version.html) | R1 095 |
| 1 | 802.3af PoE injector or PoE switch port (PoE version only) | | any | — |

Avoid the SLZB-06**M** (EFR32) for now. z2m support for that chip is listed
as experimental. A Sonoff ZBDongle-E ([GeeWiz](https://www.geewiz.co.za/accessories/185747-sonoff-zigbee-dongle-e-usb-3-gateway-antenna.html))
works, but it's USB, so it needs a udev exclusion on the bench (DESIGN §3.2).

## 3. Fixture, one per DUT (P1/P2)

Order enough for **2 fixtures** to start: blinds plus one other project or a
spare.

| Qty / fixture | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 | Raspberry Pi Pico (RP2040). Get the **H** (pre-soldered headers) version if available | Fixture brain: edge capture, step count, key drive, ADC | [PiShop — Pico](https://www.pishop.co.za/store/raspberry-pi-pico) | R83 |
| 1 | INA226 current/voltage module (0–36 V, I²C) | DUT supply voltage and current; blinds 24 V motor current. Default 0.1 Ω shunt = ±0.8 A full scale | [Micro Robotics — INA226](https://www.robotics.org.za/INA226-MOD) | R102 |
| 1 | ADS1115 16-bit ADC module | Rail checks (5 V after diode, 3V3), light sensor | [Micro Robotics — ADS1115](https://www.robotics.org.za/ADS1115-MOD) · [Botshop](https://www.botshop.co.za/shop/mod-015-16-bit-4-channel-adc-module-i2c-ads1115-131) · [DIYElectronics (DFRobot)](https://diyelectronics.co.za/store/dfrobot/4921-gravity-i2c-16-bit-analog-to-digital-converter-module.html) | — |
| 2 | MCP4725 12-bit DAC module (set addresses 0x62/0x63) | Analog stimulus: soil sensor, battery voltage (MoistureTracker) | [Micro Robotics — MCP4725](https://www.robotics.org.za/MCP4725-MOD) · [PiShop (Adafruit)](https://www.pishop.co.za/store/adafruit-12-bit-dac-wi2c-interface-mcp4725) | R29 each |
| 1 | 2-channel relay module, opto-isolated, **3.3 V-logic compatible** | Power-cut tests: ch1 DUT 5 V, ch2 24 V motor supply | [Micro Robotics — 2ch 3.3/5V](https://www.robotics.org.za/REL-2CHAN-335V) | — |
| 1 | 20-way IDC crimp connector (female) + matching 2×10 box header | The standard DUT connector (DESIGN §4.2) | [DIYElectronics — IDC 20-way](https://diyelectronics.co.za/store/connectors-wiring/2619-idc-crimp-connector-dil-20-way.html) (header: their 2×10 IDC header, SKU 9C-IDCS-2X10P) | — |
| 1 m | Ribbon cable (cut a 40-way down to 20-way if 20-way isn't stocked) | Adapter cables | [Micro Robotics — ribbon cable](https://www.robotics.org.za/cables/ribbon-cable) | — |
| 1 | Prototype board / perfboard (≈ 10×15 cm) | Fixture v1. A proper PCB comes later (phase 10) | any | — |
| 20 | 330 Ω resistors, 3.3 V zener or BAT54S clamp diodes | Channel protection on every fixture channel | any | — |
| 4 | Resistors for ÷2 dividers (e.g. 10 k + 10 k, 1 %) | `SENSE_A` / `SENSE_B` | any | — |
| 1 | 2-pin screw terminal blocks ×3, inline fuse holder + 2 A fuse | 24 V path through the fixture (never through the ribbon) | any | — |
| 1 | Dupont jumper kit (F-F, M-F) | Flying leads to sensors | any | — |

## 4. Sensors (P2)

| Qty | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 / fixture | TEMT6000 ambient-light module | Taped over the status LED: catches a reversed LED and confirms flash patterns | [Communica — TEMT6000](https://www.communica.co.za/products/bmt-temt6000-ambient-light-senso) | R29–45 |
| 1 pack | A3144E hall sensor (4-pack) + small neodymium magnet | Blinds: reference mark at Open to detect position drift during soak | [Micro Robotics — A3144E](https://www.robotics.org.za/A3144E) | R12 / 4 |
| 1 | DS18B20 waterproof probe | Stepper driver / buck temperature during soak | [Micro Robotics — DFRobot DS18B20 kit](https://www.robotics.org.za/KIT0021) · [DIYElectronics](https://www.diyelectronics.co.za/store/temperature/3665-ds18b20-waterproof-temperature-sensor-for-arduino.html) | — |

## 5. Test equipment (P2/P3)

| Qty | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 | USB logic analyzer, 24 MHz 8-ch (sigrok/PulseView compatible) | Deep dives on individual glitches; plugs into the Pi | [Micro Robotics — LOGIC-08-24](https://www.robotics.org.za/LOGIC-08-24) · [Communica](https://www.communica.co.za/products/bdd-usb-logic-analyzer-24mhz-8ch) | R193 |
| 1 | Nordic Power Profiler Kit II (nRF-PPK2) (P3) | µA sleep-current profiling for MoistureTracker; scriptable from Python | [RS Components ZA — nRF-PPK2](https://za.rs-online.com/web/p/power-motor-robotics-development-tools/2119949) | ≈ R1 965 |

## 6. Devices under test and rig parts (P1–P3)

You already build these. Extra units **dedicated to the bench** stop the
harness competing with installed units.

| Qty | Item | Why | Where | ≈ Price |
|----:|------|-----|-------|--------:|
| 1 | Complete **RollerBlinds bench unit** per `DFR-RollerBlinds/HARDWARE.md` BOM (XIAO ESP32C6, TMC2209 V1.3, stepper, buck, 1N5822, LED, keypad + RC parts, 24 V LRS-50-24) | The blinds DUT and noise rig; motor running free or on a short spare tube | your usual suppliers | — |
| 1 | Seeed **XIAO ESP32C6** (spare) | `esp-zb-common` `minimal_router` qualification DUT. Not found at SA shops in this search; order from Seeed or ask Communica / Micro Robotics to source | [Seeed Studio](https://www.seeedstudio.com) | — |
| 1–2 | **DFRobot FireBeetle 2 ESP32-C6** | DoorSensor and MoistureTracker DUTs (P3) | [Micro Robotics — DFR1075](https://www.robotics.org.za/DFR1075) · [DIYElectronics](https://www.diyelectronics.co.za/store/iot/5497-firebeetle-2-esp32-c6-iot-microcontroller-with-wifi-ble-zigbee.html) | ≈ R147 |
| 1 | Membrane keypad lead at **full installed length**, plus a matching motor cable | Worst-case noise rig: route alongside each other (DESIGN §7.4) | — | — |
| 1 | Clip-on ferrite cores, a length of shielded cable | A/B noise experiments | any | — |

## 7. Optional

| Item | Why | Where |
|------|-----|-------|
| Raspberry Pi GPIO screw-terminal board | Tidy wiring if you use the Pi's own GPIO for EN/BOOT reset lines on the bench | [PiShop](https://www.pishop.co.za/store/raspberry-pi-gpio-screw-terminal-board-header-for-raspberry-pi) |
| UPS HAT or small UPS for the Pi | Load-shedding: a soak survives an outage (the DUT power cut is then a real test too) | — |

---

## Rough budget

| Block | ≈ ZAR |
|-------|------:|
| Bench Pi (Pi 5, PSU, cooler, SSD kit, case, hub, cables) | 4 000 – 4 800 |
| Zigbee coordinator (+ PoE injector) | 1 100 – 1 400 |
| Fixtures ×2 (Pico, INA226, ADS1115, 2×DAC, relay, connectors, passives) | 900 – 1 200 |
| Sensors ×2 sets | 200 – 300 |
| Logic analyzer | 200 |
| **Phases 0–7 total** | **≈ 6 500 – 8 000** |
| + PPK2 for battery projects (P3) | + 2 000 |
| + bench DUT units | your BOM cost |
