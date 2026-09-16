#!/usr/bin/env python3
"""Watches the touchscreen for a long-press in the top-left corner and asks
the launcher backend to return home. Runs independently of whatever app is
in the foreground (react-carplay has no back button), by reading the raw
input device directly instead of going through the window manager."""

import time
import urllib.request

import evdev

DEVICE_NAME = "Waveshare  Waveshare "
ABS_X_MAX = 4096
ABS_Y_MAX = 4096
CORNER_X_FRACTION = 0.12  # left ~12% of the touch surface
CORNER_Y_FRACTION = 0.28  # top ~28% of the touch surface
HOLD_SECONDS = 1.2
API_URL = "http://localhost:8080/api/action"


def find_device():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if dev.name == DEVICE_NAME:
            return dev
    return None


def trigger_go_home():
    req = urllib.request.Request(
        API_URL,
        data=b'{"action": "go-home"}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


def in_corner(x, y):
    return x is not None and y is not None \
        and x < ABS_X_MAX * CORNER_X_FRACTION \
        and y < ABS_Y_MAX * CORNER_Y_FRACTION


def main():
    dev = None
    while dev is None:
        dev = find_device()
        if dev is None:
            time.sleep(2)

    x = y = None
    touch_down_at = None
    fired = False

    for event in dev.read_loop():
        if event.type == evdev.ecodes.EV_ABS:
            if event.code == evdev.ecodes.ABS_X:
                x = event.value
            elif event.code == evdev.ecodes.ABS_Y:
                y = event.value
        elif event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.BTN_TOUCH:
            if event.value == 1:
                touch_down_at = time.monotonic()
                fired = False
            elif event.value == 0:
                touch_down_at = None
                x = y = None

        if touch_down_at is not None and not fired and in_corner(x, y):
            if time.monotonic() - touch_down_at >= HOLD_SECONDS:
                trigger_go_home()
                fired = True


if __name__ == "__main__":
    main()
