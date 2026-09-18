const WEEKDAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];

function updateClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  document.getElementById("clock").textContent = `${hh}:${mm}`;
  const day = WEEKDAYS[now.getDay()];
  const d = String(now.getDate()).padStart(2, "0");
  const m = String(now.getMonth() + 1).padStart(2, "0");
  document.getElementById("date").textContent = `${day}, ${d}.${m}.`;
}
setInterval(updateClock, 5000);
updateClock();

async function callAction(action) {
  try {
    const res = await fetch(`/api/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    return await res.json();
  } catch (e) {
    console.error("Action failed", action, e);
    return { ok: false, error: String(e) };
  }
}

function confirmShutdown() {
  const overlay = document.createElement("div");
  overlay.className = "confirm-overlay visible";
  overlay.innerHTML = `
    <p>Wirklich herunterfahren?</p>
    <div class="confirm-actions">
      <button data-cancel>Abbrechen</button>
      <button class="danger" data-confirm>Herunterfahren</button>
    </div>`;
  document.body.appendChild(overlay);
  overlay.querySelector("[data-cancel]").onclick = () => overlay.remove();
  overlay.querySelector("[data-confirm]").onclick = () => {
    overlay.remove();
    callAction("shutdown");
  };
}

document.querySelectorAll("[data-action]").forEach((el) => {
  el.addEventListener("click", () => {
    const action = el.dataset.action;
    if (action === "shutdown") {
      confirmShutdown();
      return;
    }
    callAction(action);
  });
});

async function pollStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const dot = document.getElementById("conn-dot");
    const label = document.getElementById("conn-label");
    const sub = document.getElementById("carplay-sub");
    if (data.carplayRunning) {
      dot.className = "dot online";
      label.textContent = "CarPlay aktiv";
      sub.textContent = "Läuft";
    } else if (data.carplayDeviceConnected) {
      dot.className = "dot online";
      label.textContent = "Gerät verbunden";
      sub.textContent = "Bereit zum Start";
    } else {
      dot.className = "dot offline";
      label.textContent = "CarPlay bereit";
      sub.textContent = "Kein Gerät verbunden";
    }
    if (typeof data.temperatureC === "number") {
      document.getElementById("temp-chip").textContent = `${Math.round(data.temperatureC)}°C`;
    }
  } catch (e) {
    // Backend evtl. gerade neugestartet - naechster Poll versucht es erneut
  }
}
setInterval(pollStatus, 4000);
pollStatus();
