#!/usr/bin/env python3
"""Watches the touchscreen for a long-press in the top-left corner and asks
the launcher backend to return home. Runs independently of whatever app is
in the foreground (react-carplay has no back button), by reading the raw
input device directly instead of going through the window manager."""

import os
import signal
import time

import evdev

DEVICE_NAME = "Waveshare  Waveshare "
ABS_X_MAX = 4096
ABS_Y_MAX = 4096
CORNER_X_FRACTION = 0.12  # left ~12% of the touch surface
CORNER_Y_FRACTION = 0.28  # top ~28% of the touch surface
HOLD_SECONDS = 1.2


def find_device():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if dev.name == DEVICE_NAME:
            return dev
    return None


def trigger_go_home():
    # Killing the current 'cage' process makes kiosk-runner.sh fall through
    # to its default next iteration, which is always the launcher - so this
    # works the same whether CarPlay or the launcher itself is on screen.
    try:
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            try:
                with open(f"/proc/{pid_str}/comm") as f:
                    comm = f.read().strip()
            except OSError:
                continue
            if comm == "cage":
                os.kill(int(pid_str), signal.SIGTERM)
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
