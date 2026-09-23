#!/usr/bin/env python3
"""Pull and install a tested MMI bundle from the latest GitHub release."""

import hashlib
import argparse
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


REPOSITORY = "tim-stubbe/audi-mmi"
ASSET_NAME = "audi-mmi-update.tar.gz"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
VERSION_FILE = Path("/opt/audi-mmi/VERSION")
STATUS_FILE = Path("/var/lib/audi-mmi/update-status.json")
INSTALL_MARKER = Path("/home/mmi/.config/audi-mmi/install-update")
BACKUP_DIR = Path("/opt/audi-mmi/backups")

FILES = {
    "native-launcher/launcher.py": (Path("/opt/audi-mmi/native-launcher/launcher.py"), 0o644),
    "native-launcher/assets/alps-background.png": (Path("/opt/audi-mmi/native-launcher/assets/alps-background.png"), 0o644),
    "bin/kiosk-runner.sh": (Path("/opt/audi-mmi/bin/kiosk-runner.sh"), 0o755),
    "bin/touch-home-watcher.py": (Path("/opt/audi-mmi/bin/touch-home-watcher.py"), 0o755),
    "bin/audi-mmi-updater.py": (Path("/opt/audi-mmi/bin/audi-mmi-updater.py"), 0o755),
    "systemd/audi-mmi-kiosk.service": (Path("/etc/systemd/system/audi-mmi-kiosk.service"), 0o644),
    "systemd/audi-mmi-home-watcher.service": (Path("/etc/systemd/system/audi-mmi-home-watcher.service"), 0o644),
    "systemd/audi-mmi-update.service": (Path("/etc/systemd/system/audi-mmi-update.service"), 0o644),
    "systemd/audi-mmi-update.timer": (Path("/etc/systemd/system/audi-mmi-update.timer"), 0o644),
    "carplay/99-carlinkit.rules": (Path("/etc/udev/rules.d/99-carlinkit.rules"), 0o644),
    "fastcarplay/fastcarplay": (Path("/opt/audi-mmi/fastcarplay/fastcarplay"), 0o755),
    "fastcarplay/settings.txt": (Path("/opt/audi-mmi/fastcarplay/settings.txt"), 0o644),
    "fastcarplay/LICENSE": (Path("/opt/audi-mmi/fastcarplay/LICENSE"), 0o644),
    "fastcarplay/SOURCE.md": (Path("/opt/audi-mmi/fastcarplay/SOURCE.md"), 0o644),
}


def run(*command, check=True):
    return subprocess.run(command, check=check, text=True, capture_output=True)


def request_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Audi-MMI-Updater/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def download(url, target, progress=None):
    request = urllib.request.Request(url, headers={"User-Agent": "Audi-MMI-Updater/1"})
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
        total = int(response.headers.get("Content-Length") or 0)
        received = 0
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            output.write(chunk)
            received += len(chunk)
            if progress and total:
                progress(received, total)


def extract_safely(archive, destination):
    destination = destination.resolve()
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if member.issym() or member.islnk():
                raise RuntimeError("Links sind im Updatepaket nicht erlaubt")
            candidate = (destination / member.name).resolve()
            if destination not in candidate.parents and candidate != destination:
                raise RuntimeError("Ungültiger Pfad im Updatepaket")
            bundle.extract(member, destination)


def verify_bundle(root):
    for relative in FILES:
        if not (root / relative).is_file():
            raise RuntimeError(f"Updatepaket unvollständig: {relative}")
    run("python3", "-m", "py_compile", str(root / "native-launcher/launcher.py"),
        str(root / "bin/touch-home-watcher.py"), str(root / "bin/audi-mmi-updater.py"))
    run("bash", "-n", str(root / "bin/kiosk-runner.sh"))


def install(root, version):
    current = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unbekannt"
    backup = BACKUP_DIR / current.replace("/", "-")
    backup.mkdir(parents=True, exist_ok=True)

    for relative, (target, _mode) in FILES.items():
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)

    try:
        for relative, (target, mode) in FILES.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".new")
            shutil.copy2(root / relative, temporary)
            os.chmod(temporary, mode)
            temporary.replace(target)

        run("udevadm", "control", "--reload-rules")
        run("systemctl", "daemon-reload")
        run("systemctl", "enable", "audi-mmi-update.timer")
        if os.environ.get("AUDI_MMI_SKIP_KIOSK_RESTART") != "1":
            run("systemctl", "restart", "audi-mmi-kiosk.service", "audi-mmi-home-watcher.service")
            run("systemctl", "is-active", "--quiet", "audi-mmi-kiosk.service")
            run("systemctl", "is-active", "--quiet", "audi-mmi-home-watcher.service")
        VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    except Exception:
        for relative, (target, mode) in FILES.items():
            saved = backup / relative
            if saved.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved, target)
                os.chmod(target, mode)
        run("systemctl", "daemon-reload", check=False)
        run("systemctl", "restart", "audi-mmi-kiosk.service", "audi-mmi-home-watcher.service", check=False)
        raise

    backups = sorted(BACKUP_DIR.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True)
    for old in backups[3:]:
        if old.is_dir():
            shutil.rmtree(old, ignore_errors=True)


def write_status(current, latest, available, error=None, state="idle", progress=0, message=""):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATUS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "current": current,
        "latest": latest,
        "available": bool(available),
        "error": error,
        "state": state,
        "progress": max(0, min(100, int(progress))),
        "message": message,
    }), encoding="utf-8")
    os.chmod(temporary, 0o644)
    temporary.replace(STATUS_FILE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Nur nach Updates suchen")
    parser.add_argument("--install", action="store_true", help="Verfügbares Update installieren")
    args = parser.parse_args()

    current = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else ""
    release = request_json(API_URL)
    version = release["tag_name"]
    asset = next((item for item in release.get("assets", []) if item.get("name") == ASSET_NAME), None)
    available = version != current and asset is not None
    write_status(current, version, available, state="available" if available else "current",
                 message=(f"Version {version} ist verfügbar" if available else "System ist aktuell"))

    if version == current:
        INSTALL_MARKER.unlink(missing_ok=True)
        print(f"Audi MMI ist aktuell ({version}).")
        return

    if not asset:
        print(f"Release {version} enthält kein freigegebenes MMI-Update.")
        return

    # Boot checks only fetch release metadata. A download/install happens
    # exclusively after the driver requested it in the MMI UI.
    if not args.install and not INSTALL_MARKER.exists():
        print(f"Audi MMI Update verfügbar: {version}. Installation wartet auf Freigabe.")
        return

    with tempfile.TemporaryDirectory(prefix="audi-mmi-update-") as temp:
        temp = Path(temp)
        archive = temp / ASSET_NAME
        write_status(current, version, True, state="downloading", progress=8,
                     message="Update wird heruntergeladen")

        last_reported = [-1]

        def report_download(received, total):
            percent = 8 + int((received / total) * 47)
            if percent != last_reported[0]:
                last_reported[0] = percent
                write_status(current, version, True, state="downloading", progress=percent,
                             message="Update wird heruntergeladen")

        download(asset["browser_download_url"], archive, report_download)
        write_status(current, version, True, state="verifying", progress=60,
                     message="Update wird geprüft")
        digest = asset.get("digest") or ""
        if digest.startswith("sha256:"):
            actual = hashlib.sha256(archive.read_bytes()).hexdigest()
            if actual != digest.removeprefix("sha256:"):
                raise RuntimeError("Prüfsumme des Updatepakets stimmt nicht")
        payload = temp / "payload"
        payload.mkdir()
        extract_safely(archive, payload)
        verify_bundle(payload)
        write_status(current, version, True, state="installing", progress=78,
                     message="Neue Version wird installiert")
        install(payload, version)
    INSTALL_MARKER.unlink(missing_ok=True)
    write_status(version, version, False, state="complete", progress=100,
                 message="Update erfolgreich installiert")
    print(f"Audi MMI wurde auf {version} aktualisiert.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        current = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else ""
        try:
            previous = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = {}
        write_status(current, previous.get("latest", ""), True, error=str(exc),
                     state="error", message="Update konnte nicht installiert werden")
        raise
