# osx-usb-resolve

Resolve macOS USB devices to `/dev/cu.*` paths by serial number or product name.

## The problem

On macOS, USB serial devices show up as `/dev/cu.usbmodem40121101`, `/dev/cu.usbmodem40121201`, etc. These paths look like stable identifiers but they're not — the number encodes the **physical USB port location**, not the device itself. Plug the same board into a different port and it gets a completely different path. Plug a different board into the same port and it gets the same path.

This makes it impossible to write reliable scripts like `mavproxy.py --master /dev/cu.usbmodem40121101` — it breaks the moment you reorganize your USB hub or plug in one more device.

Unlike Linux, macOS has no `udev` rules to create stable symlinks by device identity.

## The solution

Each USB device has a burned-in serial number and a product name that never change. This tool queries `system_profiler` for the USB device tree and maps those stable identifiers back to the current `/dev/cu.*` path:

```bash
# Before: hardcoded, breaks when you replug
mavproxy.py --master /dev/cu.usbmodem40121101

# After: always finds the right device
mavproxy.py --master $(usb-resolve --by-iname tracker)
```

## Install

### Homebrew

```bash
brew install chexov/tools/usb-resolve
```

### pip / uv

```bash
pip install osx-usb-resolve
```

Or with [uv](https://docs.astral.sh/uv/):
```bash
uv tool install osx-usb-resolve
```

## Usage

```bash
# List all USB devices with their serial ports
usb-resolve --list

# Resolve by exact product name
usb-resolve --by-name "KiwiH743-wing"

# Resolve by case-insensitive substring
usb-resolve --by-iname tracker

# Resolve by USB serial number (stable across ports)
usb-resolve --by-serial 1E0042001251333236323533

# Device with multiple serial ports — pick the second one
usb-resolve --by-name "KiwiH743-wing" --index 1
```

Output is the bare `/dev/cu.*` path with no trailing newline, ready for shell substitution:

```bash
mavproxy.py --master $(usb-resolve --by-iname tracker)
```

## How it works

1. Parses `system_profiler SPUSBDataType -xml` to get USB device tree with serial numbers and location IDs
2. Maps location IDs to `/dev/cu.usbmodem*` device paths (macOS encodes the USB location in the device name)
3. Returns the matching `/dev/cu.*` path

## Requirements

- macOS (uses `system_profiler`)
- Python 3.8+
- No dependencies — stdlib only
