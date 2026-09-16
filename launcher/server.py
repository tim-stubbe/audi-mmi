#!/usr/bin/env python3
"""Audi MMI launcher backend: serves the kiosk UI and switches between the
launcher screen and the react-carplay AppImage. Runs as the unprivileged
'tim' user; shutdown/reboot work via passwordless sudo configured on the Pi."""

import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))
CARPLAY_APPIMAGE = "/opt/audi-mmi/carplay/react-carplay-4.0.5-arm64.AppImage"
CARLINKIT_VENDOR_ID = "1314"
PORT = 8080

state_lock = threading.Lock()
state = {"chromium_proc": None, "carplay_proc": None}


def start_chromium():
    with state_lock:
        if state["chromium_proc"] and state["chromium_proc"].poll() is None:
            return
        state["chromium_proc"] = subprocess.Popen([
            "chromium",
            "--no-memcheck",
            "--ozone-platform=wayland",
            "--enable-features=UseOzonePlatform",
            "--kiosk",
            "--incognito",
            "--noerrdialogs",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--check-for-update-interval=31536000",
            f"http://localhost:{PORT}/",
        ], env={**os.environ, "WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"})


def stop_chromium():
    with state_lock:
        proc = state["chromium_proc"]
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        state["chromium_proc"] = None


def start_carplay():
    with state_lock:
        if state["carplay_proc"] and state["carplay_proc"].poll() is None:
            return
        if not os.path.exists(CARPLAY_APPIMAGE):
            return False
        state["carplay_proc"] = subprocess.Popen(
            [CARPLAY_APPIMAGE, "--no-sandbox", "--ozone-platform=wayland"],
            env={**os.environ, "WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"},
        )
    stop_chromium()
    return True


def stop_carplay():
    with state_lock:
        proc = state["carplay_proc"]
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        state["carplay_proc"] = None


def go_home():
    stop_carplay()
    start_chromium()


def carplay_device_connected():
    try:
        out = subprocess.check_output(["lsusb"], text=True)
        return CARLINKIT_VENDOR_ID in out.lower().replace("0x", "")
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the journal quiet on an embedded system

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            with state_lock:
                carplay_running = bool(state["carplay_proc"] and state["carplay_proc"].poll() is None)
            self._send_json({
                "carplayDeviceConnected": carplay_device_connected(),
                "carplayRunning": carplay_running,
            })
            return
        # static file serving
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        full_path = os.path.normpath(os.path.join(LAUNCHER_DIR, path.lstrip("/")))
        if not full_path.startswith(LAUNCHER_DIR) or not os.path.isfile(full_path):
            self.send_response(404)
            self.end_headers()
            return
        content_type = "text/html"
        if full_path.endswith(".css"):
            content_type = "text/css"
        elif full_path.endswith(".js"):
            content_type = "application/javascript"
        with open(full_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/action":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            data = {}
        action = data.get("action")

        if action == "start-carplay":
            ok = start_carplay()
            self._send_json({"ok": ok is not False})
        elif action == "go-home":
            go_home()
            self._send_json({"ok": True})
        elif action == "open-vehicle":
            # Fahrzeugdaten-Seite folgt in einer spaeteren Ausbaustufe (CAN-Anbindung)
            self._send_json({"ok": True, "note": "not-yet-implemented"})
        elif action == "open-settings":
            self._send_json({"ok": True, "note": "not-yet-implemented"})
        elif action == "shutdown":
            self._send_json({"ok": True})
            subprocess.Popen(["sudo", "systemctl", "poweroff"])
        else:
            self._send_json({"ok": False, "error": "unknown action"}, status=400)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    start_chromium()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
