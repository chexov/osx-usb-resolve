#!/usr/bin/env python3
"""Resolve USB device to /dev/cu.* path by serial number or product name.

Usage:
    usb-resolve.py --by-serial 1E0042001251333236323533
    usb-resolve.py --by-name KiwiH743-wing
    usb-resolve.py --by-name KiwiH743-wing --index 1   # second serial port
    usb-resolve.py --by-iname tracker                    # case-insensitive substring match
    usb-resolve.py --list                                # show all USB serial devices
"""

import argparse
import glob
import plistlib
import subprocess
import sys


def get_usb_devices():
    """Parse system_profiler for USB devices with serial numbers."""
    raw = subprocess.check_output(
        ["system_profiler", "SPUSBDataType", "-xml"], stderr=subprocess.DEVNULL
    )
    data = plistlib.loads(raw)
    devices = []

    def walk(items):
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("_name", "")
            serial = item.get("serial_num", "")
            loc = item.get("location_id", "")
            if serial:
                loc_hex = ""
                if isinstance(loc, str):
                    loc_hex = loc.split()[0].replace("0x", "")
                    # macOS names /dev/cu.* from the location as an int, so
                    # drop leading zeros ("01140000" -> "1140000")
                    if loc_hex:
                        loc_hex = "%x" % int(loc_hex, 16)
                elif isinstance(loc, int):
                    loc_hex = "%x" % loc
                devices.append({"name": name, "serial": serial, "location": loc_hex})
            walk(item.get("_items", []))

    for section in data:
        walk(section.get("_items", []))
    return devices


def location_to_devs(location, serial=""):
    """Find /dev/cu.usbmodem* paths matching a USB location ID or serial number."""
    devs = []
    prefix = location.rstrip("0")
    if prefix:
        devs = sorted(glob.glob("/dev/cu.usbmodem%s*" % prefix))
    # macOS sometimes names ports by serial number instead of location
    if not devs and serial:
        devs = sorted(glob.glob("/dev/cu.usbmodem%s*" % serial))
    return devs


def main():
    parser = argparse.ArgumentParser(description="Resolve USB device to /dev path")
    parser.add_argument("--by-serial", help="USB serial number")
    parser.add_argument("--by-name", help="USB product name (exact)")
    parser.add_argument(
        "--by-iname", help="case-insensitive substring match on product name"
    )
    parser.add_argument("--index", type=int, default=0, help="port index (default: 0)")
    parser.add_argument(
        "--list", action="store_true", help="list all USB serial devices"
    )
    args = parser.parse_args()

    devices = get_usb_devices()

    if args.list:
        for d in devices:
            devs = location_to_devs(d["location"], d["serial"])
            ports = ", ".join(devs) if devs else "(no serial port)"
            print("%s  serial=%s  %s" % (d["name"], d["serial"], ports))
        return

    if not args.by_serial and not args.by_name and not args.by_iname:
        parser.print_help()
        sys.exit(1)

    match = None
    for d in devices:
        if args.by_serial and d["serial"] == args.by_serial:
            match = d
            break
        if args.by_name and d["name"] == args.by_name:
            match = d
            break
        if args.by_iname and args.by_iname.lower() in d["name"].lower():
            match = d
            break

    if match is None:
        key = args.by_serial or args.by_name or args.by_iname
        print("device not found: %s" % key, file=sys.stderr)
        sys.exit(1)

    devs = location_to_devs(match["location"], match["serial"])
    if not devs:
        print("no /dev/cu.* port for %s" % match["name"], file=sys.stderr)
        sys.exit(1)

    if args.index >= len(devs):
        print(
            "index %d out of range, device has %d port(s)" % (args.index, len(devs)),
            file=sys.stderr,
        )
        sys.exit(1)

    sys.stdout.write(devs[args.index])


if __name__ == "__main__":
    main()
