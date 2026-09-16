function updateClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  document.getElementById("clock").textContent = `${hh}:${mm}`;
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

document.querySelectorAll(".tile").forEach((tile) => {
  tile.addEventListener("click", () => {
    const action = tile.dataset.action;
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
    const dot = document.getElementById("status");
    dot.className = "status-dot " + (data.carplayDeviceConnected ? "online" : "offline");
  } catch (e) {
    // backend not reachable yet, ignore
  }
}
setInterval(pollStatus, 4000);
pollStatus();
