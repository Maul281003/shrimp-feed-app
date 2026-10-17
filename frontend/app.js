const API_BASE = `${window.location.origin}/api/v1`;

async function checkHealth() {
  const el = document.getElementById("api-status");
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    const data = await res.json();
    if (data.status === "ok" && data.database === "ok") {
      el.textContent = "terhubung";
      el.className = "badge ok";
    } else {
      el.textContent = "DB bermasalah";
      el.className = "badge error";
    }
  } catch {
    el.textContent = "tidak terhubung";
    el.className = "badge error";
  }
}

function detectDisplayMode() {
  const el = document.getElementById("display-mode");
  const standalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;
  el.textContent = standalone ? "terinstall" : "browser";
  el.className = standalone ? "badge ok" : "badge";
}

checkHealth();
detectDisplayMode();
setInterval(checkHealth, 30000);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .catch((err) => console.warn("Service worker gagal:", err));
  });
}