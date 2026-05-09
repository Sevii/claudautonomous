# Using `rp-hal` with the Raspberry Pi Pico 2 W

A concentrated guide for getting Rust running on the Raspberry Pi **Pico 2 W**
(RP2350 + CYW43439 Wi‑Fi/BT) using the [`rp-hal`](https://github.com/rp-rs/rp-hal)
project.

---

## 1. What you actually use

The Pico 2 W has two chips that matter to your firmware:

| Chip       | Role                                       | Rust crate(s)                                                     |
|------------|--------------------------------------------|-------------------------------------------------------------------|
| RP2350     | Dual Cortex‑M33 (or Hazard3 RISC‑V) MCU    | `rp235x-hal` (HAL) + `rp235x-pac` (PAC)                           |
| CYW43439   | 2.4 GHz Wi‑Fi + Bluetooth + onboard LED    | `cyw43` + `cyw43-pio` (from the [embassy](https://github.com/embassy-rs/embassy) repo) |

Important facts:

* **There is no dedicated BSP** for the Pico 2 / Pico 2 W in
  [`rp-hal-boards`](https://github.com/rp-rs/rp-hal-boards). You depend on
  `rp235x-hal` directly and supply your own `memory.x`. (The `rp-hal-boards`
  repo only ships RP2040‑era boards such as `rp-pico`.)
* The **onboard LED is wired to GPIO 0 of the CYW43439**, *not* to an RP2350
  GPIO. Plain `OutputPin` will not blink it — you must bring up the Wi‑Fi chip
  first, even if you never use the network. (This was true on the Pico W and
  carries over to the Pico 2 W.)
* The CYW43439 is connected via a non‑standard half‑duplex 3‑wire SPI driven
  by **PIO**, on the following RP2350 pins:
    * `PIN_23` — PWR (power‑on / regulator enable)
    * `PIN_24` — DIO (combined MOSI/MISO)
    * `PIN_25` — CS
    * `PIN_29` — CLK
* The Pico 2 W has **4 MiB** of flash. The example `memory.x` in the rp-hal
  tree defaults to 2 MiB — bump it.

---

## 2. Toolchain

```bash
# Rust nightly is not required; rp235x-hal needs Rust >= 1.82
rustup target add thumbv8m.main-none-eabihf      # Cortex-M33 (default)
# Optional: build for the Hazard3 RISC-V cores instead
rustup target add riscv32imac-unknown-none-elf

# Loader. Pico 2 / Pico 2 W require recent picotool (>= 2.0) for RP2350 support.
# Install from https://github.com/raspberrypi/picotool
cargo install --locked elf2uf2-rs    # alternative if you prefer UF2 + BOOTSEL
```

`picotool` is what `cargo run` will invoke. It can flash either over USB
(BOOTSEL mode: hold the BOOTSEL button while plugging in) or over a Picoprobe /
Debug Probe via SWD.

---

## 3. Project layout

```
my-pico2w/
├── .cargo/
│   └── config.toml
├── Cargo.toml
├── memory.x
└── src/
    └── main.rs
```

### `Cargo.toml`

```toml
[package]
name = "my-pico2w"
version = "0.1.0"
edition = "2021"
rust-version = "1.82"

[dependencies]
cortex-m       = "0.7.2"
cortex-m-rt    = "0.7"
embedded-hal   = "1.0.0"
panic-halt     = "1"

# Core HAL — pick the features you need.
#   rt                  : pulls in cortex-m-rt vector table glue
#   critical-section-impl : provides the critical-section impl for the chip
#   binary-info         : enables the rp_* macros used for picotool metadata
#   defmt               : defmt-encoded logging on supported peripherals
rp235x-hal = { version = "0.4", features = [
    "binary-info",
    "critical-section-impl",
    "rt",
    "defmt",
] }

# --- Optional: Wi-Fi / onboard LED on the CYW43439 ----------------------------
# These come from the embassy monorepo. The `cyw43` crate is async-only, so
# you'll typically pair it with embassy-executor + embassy-rp.
embassy-executor = { version = "0.6", features = ["arch-cortex-m", "executor-thread", "integrated-timers"] }
embassy-rp       = { version = "0.2", features = ["rp235xa", "time-driver", "critical-section-impl"] }
embassy-time     = "0.3"
cyw43            = { version = "0.2", features = ["firmware-logs"] }
cyw43-pio        = "0.2"
static_cell      = "2"
```

> Mixing `rp235x-hal` and `embassy-rp` in the same binary is fine for many
> simple cases (they share the underlying PAC), but for non‑trivial Wi‑Fi
> projects most people pick **one** stack — either pure `rp235x-hal` for
> bare‑metal blinky/peripheral work, or **embassy‑rp + cyw43** when you need
> the radio. The cyw43 driver is async; there is no blocking driver today.

### `memory.x`  (Pico 2 W: 4 MiB flash)

Copy from
[`rp235x-hal-examples/memory.x`](https://github.com/rp-rs/rp-hal/blob/main/rp235x-hal-examples/memory.x)
and bump `FLASH` to 4096K:

```ld
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K   /* Pico 2 / Pico 2 W: 4 MiB */
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K    /* striped across SRAM0..7 */
    SRAM4 : ORIGIN = 0x20080000, LENGTH = 4K
    SRAM5 : ORIGIN = 0x20081000, LENGTH = 4K
}

SECTIONS {
    .start_block : ALIGN(4) {
        __start_block_addr = .;
        KEEP(*(.start_block));
    } > FLASH

    .text : { *(.text*) } > FLASH

    .bi_entries : ALIGN(4) {
        __bi_entries_start = .;
        KEEP(*(.bi_entries));
        __bi_entries_end   = .;
    } > FLASH

    .end_block : ALIGN(4) {
        __end_block_addr = .;
        KEEP(*(.end_block));
    } > FLASH

    __flash_binary_end = .;
} INSERT AFTER .text;
```

The full upstream version has additional helper symbols and the SRAM bank
layout — prefer copying that file verbatim and only changing `LENGTH`.

### `.cargo/config.toml`

```toml
[build]
target = "thumbv8m.main-none-eabihf"

[target.thumbv8m.main-none-eabihf]
rustflags = [
    "-C", "link-arg=--nmagic",
    "-C", "link-arg=-Tlink.x",
    "-C", "link-arg=-Tdefmt.x",
    "-C", "target-cpu=cortex-m33",
]
runner = "picotool load -u -v -x -t elf"

[alias]
build-arm = "build --target thumbv8m.main-none-eabihf"
run-arm   = "run   --target thumbv8m.main-none-eabihf"
```

`picotool load -u -v -x -t elf` = update only changed sectors, verify, execute,
input format ELF.

---

## 4. Bare‑metal "hello world" (RP2350 only, no Wi‑Fi)

This is the standard `rp235x-hal` blinky — adapted from
[`rp235x-hal-examples/src/bin/blinky.rs`](https://github.com/rp-rs/rp-hal/blob/main/rp235x-hal-examples/src/bin/blinky.rs).
It will **not** light the onboard LED on the Pico 2 W (that LED is on the
CYW43); use it on a GPIO with an external LED, or as a sanity check that
toolchain + flashing works.

```rust
#![no_std]
#![no_main]

use embedded_hal::delay::DelayNs;
use embedded_hal::digital::OutputPin;
use panic_halt as _;
use rp235x_hal as hal;

/// Tell the boot ROM this is a normal secure executable image.
#[link_section = ".start_block"]
#[used]
pub static IMAGE_DEF: hal::block::ImageDef = hal::block::ImageDef::secure_exe();

/// Metadata that `picotool info` will show.
#[link_section = ".bi_entries"]
#[used]
pub static PICOTOOL_ENTRIES: [hal::binary_info::EntryAddr; 4] = [
    hal::binary_info::rp_cargo_bin_name!(),
    hal::binary_info::rp_cargo_version!(),
    hal::binary_info::rp_program_description!(c"Pico 2 W blinky"),
    hal::binary_info::rp_program_build_attribute!(),
];

const XTAL_HZ: u32 = 12_000_000;

#[hal::entry]
fn main() -> ! {
    let mut pac = hal::pac::Peripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);

    let clocks = hal::clocks::init_clocks_and_plls(
        XTAL_HZ,
        pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
        &mut pac.RESETS, &mut watchdog,
    ).unwrap();

    let sio   = hal::Sio::new(pac.SIO);
    let pins  = hal::gpio::Pins::new(
        pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS,
    );
    let mut timer = hal::Timer::new_timer0(pac.TIMER0, &mut pac.RESETS, &clocks);

    // Wire an LED+resistor to e.g. GPIO 15 — GPIO 25 on this board is the
    // CYW43 chip‑select, not a free pin.
    let mut led = pins.gpio15.into_push_pull_output();

    loop {
        led.set_high().unwrap();
        timer.delay_ms(500);
        led.set_low().unwrap();
        timer.delay_ms(500);
    }
}
```

Build and flash (with the Pico 2 W in BOOTSEL mode, or attached via a Debug
Probe):

```bash
cargo run --release
```

Verify the metadata after flashing:

```bash
picotool info -a
```

---

## 5. Blinking the *actual* onboard LED (over the CYW43)

Because the LED hangs off the CYW43439, you have to bring up the radio chip.
The realistic path is **embassy + cyw43**, not pure `rp235x-hal`. Outline:

```rust
#![no_std]
#![no_main]

use cyw43_pio::PioSpi;
use embassy_executor::Spawner;
use embassy_rp::bind_interrupts;
use embassy_rp::gpio::{Level, Output};
use embassy_rp::peripherals::{DMA_CH0, PIO0};
use embassy_rp::pio::{InterruptHandler, Pio};
use embassy_time::{Duration, Timer};
use static_cell::StaticCell;
use {defmt_rtt as _, panic_probe as _};

bind_interrupts!(struct Irqs {
    PIO0_IRQ_0 => InterruptHandler<PIO0>;
});

// Firmware blobs — see "Firmware blobs" section below.
const FW:  &[u8] = include_bytes!("../cyw43-firmware/43439A0.bin");
const CLM: &[u8] = include_bytes!("../cyw43-firmware/43439A0_clm.bin");

#[embassy_executor::task]
async fn cyw43_task(
    runner: cyw43::Runner<'static, Output<'static>, PioSpi<'static, PIO0, 0, DMA_CH0>>,
) -> ! {
    runner.run().await
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_rp::init(Default::default());

    let pwr = Output::new(p.PIN_23, Level::Low);
    let cs  = Output::new(p.PIN_25, Level::High);
    let mut pio = Pio::new(p.PIO0, Irqs);
    let spi = PioSpi::new(
        &mut pio.common, pio.sm0, pio.irq0,
        cs, p.PIN_24, p.PIN_29, p.DMA_CH0,
    );

    static STATE: StaticCell<cyw43::State> = StaticCell::new();
    let state = STATE.init(cyw43::State::new());
    let (_net_device, mut control, runner) = cyw43::new(state, pwr, spi, FW).await;
    spawner.spawn(cyw43_task(runner)).unwrap();

    control.init(CLM).await;
    control.set_power_management(cyw43::PowerManagementMode::PowerSave).await;

    loop {
        control.gpio_set(0, true).await;   // LED on  (CYW43 GPIO 0)
        Timer::after(Duration::from_millis(500)).await;
        control.gpio_set(0, false).await;  // LED off
        Timer::after(Duration::from_millis(500)).await;
    }
}
```

### Firmware blobs

The CYW43439 needs two binary blobs that ship under a separate license and
**are not** in `rp-hal`:

* `43439A0.bin`     — main firmware
* `43439A0_clm.bin` — Country Locale Matrix (regulatory data)

Grab them from the embassy repo:

```bash
mkdir -p cyw43-firmware
curl -L -o cyw43-firmware/43439A0.bin     https://github.com/embassy-rs/embassy/raw/main/cyw43-firmware/43439A0.bin
curl -L -o cyw43-firmware/43439A0_clm.bin https://github.com/embassy-rs/embassy/raw/main/cyw43-firmware/43439A0_clm.bin
```

For Bluetooth you additionally need `43439A0_btfw.bin`.

---

## 6. Connecting to Wi‑Fi

Once `control.init(CLM).await` has run, joining an AP is a one‑liner:

```rust
match control.join_wpa2("my-ssid", "my-pass").await {
    Ok(())  => defmt::info!("joined"),
    Err(e)  => defmt::warn!("join failed: status={}", e.status),
}
```

For TCP/UDP, layer `embassy-net` on top of the `_net_device` returned by
`cyw43::new`. The embassy repo's
[`examples/rp235x`](https://github.com/embassy-rs/embassy/tree/main/examples/rp235x)
folder has working `wifi_tcp_server`, `wifi_webrequest`, and `bluetooth`
examples that target the Pico 2 W exactly.

---

## 7. Useful examples to crib from

All under
[`rp-hal/rp235x-hal-examples/src/bin`](https://github.com/rp-rs/rp-hal/tree/main/rp235x-hal-examples/src/bin):

| Example                       | Shows                                              |
|-------------------------------|----------------------------------------------------|
| `blinky.rs`                   | Minimal `rp235x-hal` skeleton, IMAGE_DEF, picotool |
| `binary_info_demo.rs`         | All `binary_info::rp_*` macros for `picotool info` |
| `gpio_irq_example.rs`         | GPIO interrupts                                    |
| `i2c.rs` / `i2c_async.rs`     | I²C (blocking and async)                           |
| `spi.rs` / `spi_dma.rs`       | SPI, with and without DMA                          |
| `uart.rs` / `uart_dma.rs`     | UART                                               |
| `pwm_blink.rs`                | PWM                                                |
| `adc.rs` / `adc_fifo_dma.rs`  | ADC, including FIFO + DMA                          |
| `pio_blink.rs`, `pio_dma.rs`  | PIO state machines                                 |
| `multicore_fifo_blink.rs`     | Running code on core 1                             |
| `usb.rs`                      | USB CDC serial                                     |
| `watchdog.rs`                 | Watchdog                                           |
| `arch_flip.rs`                | Switching between Arm and RISC‑V cores at runtime  |

---

## 8. Building for RISC‑V (optional)

The RP2350 has two Hazard3 RISC‑V cores selectable via OTP / image header.
To target them:

```bash
rustup target add riscv32imac-unknown-none-elf
cargo build --target riscv32imac-unknown-none-elf --release
```

You will need the upstream `rp235x_riscv.x` linker script (in
`rp235x-hal-examples`) and a `runner` line for that target in `.cargo/config.toml`.
Note: **`cyw43` and most embassy crates only run on the Arm cores today.**

---

## 9. Common gotchas

* **Onboard LED won't blink with plain GPIO.** It's on the CYW43; you must
  initialise the radio chip (Section 5).
* **`picotool` says "no RP2040 device found".** Update picotool to ≥ 2.0;
  older builds don't recognise RP2350.
* **Linker error about missing `.start_block` / `.end_block`.** Your
  `memory.x` is for RP2040, not RP2350. Use the rp235x version.
* **Image runs once and resets.** `IMAGE_DEF` is missing or not in the
  `.start_block` section — without it the boot ROM rejects the image.
* **2 MiB flash limit.** Default `memory.x` ships with `LENGTH = 2048K`; the
  Pico 2 W has 4 MiB — bump it or large binaries silently truncate.
* **Mixing `rp235x-hal` and `embassy-rp` peripheral handles.** Each crate
  thinks it owns the PAC singletons. Pick one to construct peripherals.

---

## Sources

* [rp-rs/rp-hal](https://github.com/rp-rs/rp-hal) — main HAL repo
* [`rp235x-hal` on crates.io](https://crates.io/crates/rp235x-hal)
* [`rp235x-hal-examples`](https://github.com/rp-rs/rp-hal/tree/main/rp235x-hal-examples)
* [rp-rs/rp-hal-boards](https://github.com/rp-rs/rp-hal-boards) (RP2040 BSPs only)
* [embassy-rs/embassy `cyw43` driver](https://github.com/embassy-rs/embassy/tree/main/cyw43)
* [embassy `examples/rp235x`](https://github.com/embassy-rs/embassy/tree/main/examples/rp235x)
* [Raspberry Pi: "Rust on RP2350"](https://www.raspberrypi.com/news/rust-on-rp2350/)
* [Pico 2 W datasheet](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)
* [RP2350 datasheet](https://rptl.io/rp2350-datasheet)
