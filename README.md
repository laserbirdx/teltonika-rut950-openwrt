![OpenWrt on Teltonika RUT950](assets/banner.webp)

# OpenWrt on Teltonika RUT950 (RUT955 image)

Install guide for official OpenWrt 25.12.5 on the Teltonika RUT950 (Qualcomm Atheros AR9344,
16 MiB NOR flash, built-in LTE modem). OpenWrt has no RUT950 profile. The RUT950 uses the same
SoC, flash layout and partition table as the RUT955, and runs the RUT955 image.

Prebuilt images (unmodified official builds) are on the [Releases](../../releases/latest) page.

> **Unofficial.** This is not a Teltonika or OpenWrt document. Installing replaces RutOS.
> Take a full flash backup first (see below). You do this at your own risk.

## Which image: `rut955` or `rut955-h7v3c0`

OpenWrt ships **two** RUT955 profiles. They differ in the GPIO expander that drives the extra
LEDs, digital I/O and the modem power/reset lines. Our RUT950 units run the
**`rut955-h7v3c0`** image.

| Profile | GPIO expander | Image name |
|---|---|---|
| `teltonika_rut955` | 74HC595 shift registers on SPI | `openwrt-25.12.5-ath79-generic-teltonika_rut955-*` |
| `teltonika_rut955-h7v3c0` | NXP PCA9539 on I2C, address `0x74` | `openwrt-25.12.5-ath79-generic-teltonika_rut955-h7v3c0-*` |

Source: the OpenWrt commits that added the two boards
([`d1130ad265b9`](https://github.com/openwrt/openwrt/commit/d1130ad265b9),
[`aa4a33ac6256`](https://github.com/openwrt/openwrt/commit/aa4a33ac6256)) and their device
trees.

The release on this page contains the **`rut955-h7v3c0`** image. It is the one we installed and
booted on our RUT950 units.

## Hardware

Measured on a RUT950 (product code `RUT950101030`, hardware revision `0505`, RutOS
`RUT9XX_R_00.06.09.2`):

| Component | Details |
|---|---|
| SoC | Qualcomm Atheros AR9344 rev 3, MIPS 74Kc @ 560 MHz |
| RAM | 128 MiB DDR2 |
| Flash | 16 MiB SPI-NOR, Winbond W25Q128 |
| Ethernet | 4x 10/100: 3x LAN + 1x WAN |
| Wi-Fi | AR9344 built-in, 2.4 GHz 802.11n 2x2 |
| LTE modem | Huawei ME909u-521 (USB ID `12d1:1573`) on this unit. Other RUT9xx units ship other modules (e.g. Quectel EC25) |
| SIM | 2 slots, switched by GPIO |
| Stock firmware | RutOS 6 (OpenWrt CC based), Linux 3.18.44 |

The RUT955 adds RS232, RS485, digital/analog I/O, GPS and a microSD slot on top of this.

### Flash layout

Identical in RutOS and in OpenWrt:

| Offset | Size | Name | Notes |
|---|---|---|---|
| `0x000000` | 128 KiB | `u-boot` | |
| `0x020000` | 64 KiB | `config` | MAC address, product data |
| `0x030000` | 64 KiB | `art` | Wi-Fi calibration, unique per unit |
| `0x040000` | 15552 KiB | `firmware` | kernel + rootfs |
| `0xf70000` | 576 KiB | `event-log` | RutOS event log |

## Installation

### 1. Back up the flash

Do this from RutOS, before anything else. `art` and `config` are unique to your unit.

[`tools/backup_mtd.py`](tools/backup_mtd.py) reads every partition over SSH, compares each file
with an MD5 computed on the router, and assembles a full 16 MiB image. It pauses the RutOS event
logger while reading so `event-log` does not change mid-copy.

```sh
# needs Python 3 and an SSH client; sshpass only if you want to pass the password via SSHPASS
SSHPASS='your-router-password' python3 tools/backup_mtd.py rut-backup/ --host 192.168.1.1
```

RutOS runs an old Dropbear. The script already enables the legacy SSH algorithms it needs
(`ssh-rsa`, `diffie-hellman-group14-sha1`).

### 2. Flash the factory image from the RutOS web UI

Tested on a RUT950 with RutOS `RUT9XX_R_00.06.09.2`.

In the RutOS web UI, go to the firmware upgrade page and upload
`openwrt-25.12.5-ath79-generic-teltonika_rut955-h7v3c0-squashfs-factory.bin`.
**Uncheck "keep settings".**

After the reboot OpenWrt is at `192.168.1.1`.

### 3. Upgrades

Use the `squashfs-sysupgrade.bin` image from LuCI or `sysupgrade` as usual.

## Default configuration (official image)

| Setting | Value |
|---|---|
| LAN | 3 LAN ports, `192.168.1.1`, DHCP server |
| WAN | WAN port (`eth1`), DHCP client |
| Login | `root`, no password |
| Wi-Fi | disabled |
| Web UI | LuCI |
| Modem packages | `kmod-usb-net-qmi-wwan`, `kmod-usb-serial-option`, `kmod-usb-acm`, `uqmi` |

Set a root password on first login.

## License

This guide and the script's documentation are licensed under [CC BY 4.0](LICENSE).
[`tools/`](tools) is licensed under the [MIT license](LICENSE-tools).

The firmware images in the releases are unmodified official OpenWrt 25.12.5 builds, licensed
under GPL-2.0. Source code: [openwrt/openwrt @ v25.12.5](https://github.com/openwrt/openwrt/tree/v25.12.5),
official downloads: [downloads.openwrt.org](https://downloads.openwrt.org/releases/25.12.5/targets/ath79/generic/).
