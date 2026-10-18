const token = localStorage.getItem("token");
if (!token) window.location.href = "/login.html";

const headers = { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" };

async function api(path, opts = {}) {
  const res = await fetch(`/api/v1${path}`, { ...opts, headers: { ...headers, ...(opts.headers || {}) } });
  if (res.status === 401) { localStorage.removeItem("token"); window.location.href = "/login.html"; return null; }
  return res;
}

function openModal(id) { document.getElementById(id).classList.add("active"); }
function closeModals() { document.querySelectorAll(".modal-overlay").forEach(el => el.classList.remove("active")); }
document.querySelectorAll(".btn-close-modal").forEach(btn => btn.onclick = closeModals);

document.getElementById("logout").onclick = () => { localStorage.removeItem("token"); window.location.href = "/login.html"; };

let feedChartInstance = null;
let hopperChartInstances = [];
let farmsCache = [];

async function loadMe() {
  const res = await api("/auth/me");
  if (!res || !res.ok) return;
  const me = await res.json();
  document.getElementById("greet-name").textContent = `Hai, ${me.full_name.split(' ')[0]}!`;
}

async function loadFarms() {
  const res = await api("/farms");
  if (!res || !res.ok) return; // Proteksi jika API error
  farmsCache = await res.json();
}

async function loadAnalytics(farmId) {
  const res = await api(`/farms/${farmId}/analytics`);
  if (!res || !res.ok) return; // Proteksi jika API error
  const data = await res.json();
  document.getElementById("val-fcr").textContent = data.fcr;
  document.getElementById("val-biomass").textContent = data.current_biomass_kg;
  document.getElementById("val-feed").textContent = data.total_feed_kg;
}

async function loadCharts(farmId) {
  const res = await api(`/farms/${farmId}/charts`);
  if (!res || !res.ok) return; // Proteksi jika API error
  const data = await res.json();
  renderFeedChart(data.trend?.labels || [], data.trend?.values || []);
  renderHoppers(data.hoppers || []);
  checkEmptyFeed(data.hoppers || []);
}

function checkEmptyFeed(hoppers) {
  if (!Array.isArray(hoppers)) return;
  const emptyDevices = hoppers.filter(h => h.current <= 0.1);
  if (emptyDevices.length > 0) {
    const listEl = document.getElementById("empty-device-list");
    listEl.innerHTML = emptyDevices.map(d => `
      <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0; border-bottom: 1px solid rgba(239, 68, 68, 0.2);">
        <i class="fa-solid fa-circle-xmark" style="color: var(--red);"></i>
        <span style="font-weight: 700; color: var(--text-main);">${d.name}</span>
      </div>
    `).join("");
    openModal("modal-empty-alert");
  }
}

async function loadDevices() {
  const el = document.getElementById("devices");
  if (!farmsCache.length) { el.innerHTML = `<p class="muted">Tambah tambak dulu.</p>`; return; }
  
  const all = [];
  for (const f of farmsCache) {
    const res = await api(`/devices?farm_id=${f.id}`);
    if (!res || !res.ok) continue;
    const devs = await res.json();
    devs.forEach(d => all.push({ ...d, farm_name: f.name }));
  }
  
  const onlineCount = all.filter(d => d.status === 'online').length;
  document.getElementById("val-devices").textContent = onlineCount;
  
  if (!all.length) { el.innerHTML = `<p class="muted">Belum ada alat.</p>`; return; }
  
  el.innerHTML = all.map(d => `
    <div class="list-item" onclick="window.location.href='/device.html?id=${d.id}'" style="cursor: pointer;">
      <div>
        <div class="item-title">
          <span class="dot ${d.status === 'online' ? 'online' : 'offline'}"></span>
          ${d.name || d.serial}
        </div>
        <div class="item-sub">${d.serial}</div>
      </div>
      <div style="color: var(--text-muted);"><i class="fa-solid fa-chevron-right"></i></div>
    </div>`).join("");
}

function renderFeedChart(labels, data) {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const textColor = isLight ? '#0F172A' : '#94A3B8';
  const gridColor = isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';

  const ctxBar = document.getElementById('feedChart').getContext('2d');
  if (feedChartInstance) feedChartInstance.destroy();
  
  feedChartInstance = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Pakan (kg)',
        data: data,
        backgroundColor: 'rgba(6, 182, 212, 0.8)',
        borderRadius: 8,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { display: false, beginAtZero: true, grid: { color: gridColor } },
        x: { grid: { display: false }, ticks: { color: textColor, font: { family: 'Outfit', size: 10 } } }
      }
    }
  });
}

function renderHoppers(hoppers) {
  const container = document.getElementById("hopper-charts-grid");
  hopperChartInstances.forEach(c => c.destroy());
  hopperChartInstances = [];
  container.innerHTML = "";

  if (!Array.isArray(hoppers) || !hoppers.length) {
    container.innerHTML = `<p class="muted" style="grid-column: 1 / -1; text-align: center;">Belum ada alat terpasang.</p>`;
    return;
  }

  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const textColor = isLight ? '#0F172A' : '#F8FAFC';

  hoppers.forEach((h, index) => {
    let percent = (h.current / h.max) * 100;
    if (percent > 100) percent = 100;
    if (percent < 0) percent = 0;
    
    let color = '#10B981';
    if (percent <= 20) color = '#EF4444';
    else if (percent <= 50) color = '#F59E0B';

    const div = document.createElement("div");
    div.style.textAlign = "center";
    div.style.position = "relative";

    const canvas = document.createElement("canvas");
    canvas.id = `hopper-chart-${index}`;
    canvas.width = 90;
    canvas.height = 90;
    div.appendChild(canvas);

    const labelCenter = document.createElement("div");
    labelCenter.style.position = "absolute";
    labelCenter.style.top = "50%";
    labelCenter.style.left = "50%";
    labelCenter.style.transform = "translate(-50%, -50%)";
    labelCenter.style.fontWeight = "800";
    labelCenter.style.fontSize = "0.9rem";
    labelCenter.style.color = textColor;
    labelCenter.innerHTML = `${Math.round(percent)}%`;
    div.appendChild(labelCenter);

    const textName = document.createElement("div");
    textName.style.fontSize = "0.8rem";
    textName.style.marginTop = "8px";
    textName.style.color = textColor;
    textName.style.fontWeight = "600";
    textName.textContent = h.name;
    div.appendChild(textName);

    const textDetail = document.createElement("div");
    textDetail.style.fontSize = "0.7rem";
    textDetail.style.color = "var(--text-muted)";
    textDetail.textContent = `${h.current} / ${h.max} kg`;
    div.appendChild(textDetail);

    container.appendChild(div);

    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Terisi', 'Kosong'],
        datasets: [{
          data: [h.current, h.max - h.current > 0 ? h.max - h.current : 0],
          backgroundColor: [color, isLight ? '#E2E8F0' : '#1E293B'],
          borderWidth: 0,
          cutout: '80%'
        }]
      },
      options: {
        responsive: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        animation: { animateScale: true }
      }
    });
    hopperChartInstances.push(chart);
  });
}

// ACTIONS
document.getElementById("btn-save-farm").onclick = async () => {
  const name = document.getElementById("inp-farm-name").value;
  if (!name) return;
  const res = await api("/farms", { method: "POST", body: JSON.stringify({ name }) });
  if (res && res.ok) { 
    closeModals(); 
    await loadFarms(); 
    await loadDevices(); 
    document.getElementById("inp-farm-name").value = ""; 
  }
};

document.getElementById("btn-save-stock").onclick = async () => {
  if (!farmsCache.length) return alert("Tambah tambak dulu");
  const body = {
    brand_name: document.getElementById("inp-stock-brand").value,
    quantity_kg: parseFloat(document.getElementById("inp-stock-qty").value),
    min_threshold_kg: parseFloat(document.getElementById("inp-stock-min").value)
  };
  if (!body.brand_name) return;
  const res = await api(`/farms/${farmsCache[0].id}/stocks`, { method: "POST", body: JSON.stringify(body) });
  if (res && res.ok) { 
    closeModals(); 
    await loadCharts(farmsCache[0].id); 
    document.getElementById("inp-stock-brand").value = "";
  }
};

document.getElementById("btn-save-sampling").onclick = async () => {
  if (!farmsCache.length) return alert("Tambah tambak dulu");
  const body = {
    abw_gram: parseFloat(document.getElementById("inp-abw").value),
    population: parseInt(document.getElementById("inp-pop").value)
  };
  const res = await api(`/farms/${farmsCache[0].id}/samplings`, { method: "POST", body: JSON.stringify(body) });
  if (res && res.ok) { closeModals(); await loadAnalytics(farmsCache[0].id); }
};

document.getElementById("btn-save-pair").onclick = async () => {
  if (!farmsCache.length) return alert("Tambah tambak dulu.");
  const serial = document.getElementById("inp-pair-serial").value;
  if (!serial) return;
  
  const gwRes = await api(`/gateways?farm_id=${farmsCache[0].id}`);
  let gws = gwRes ? await gwRes.json() : [];
  
  if (gws.length === 0) {
    const newGwRes = await api("/gateways", {
      method: "POST",
      body: JSON.stringify({
        farm_id: farmsCache[0].id,
        serial: `GW-AUTO-${farmsCache[0].id.substring(0, 6).toUpperCase()}`,
        name: "Gateway Otomatis"
      })
    });
    if (newGwRes && newGwRes.ok) {
      gws = [await newGwRes.json()];
    } else {
      return alert("Gagal membuat Gateway otomatis.");
    }
  }
  
  const res = await api("/devices/pair", { method: "POST", body: JSON.stringify({ serial: serial.trim(), gateway_id: gws[0].id }) });
  if (res && res.ok) { 
    closeModals(); 
    await loadFarms(); 
    await loadDevices(); 
    document.getElementById("inp-pair-serial").value = "";
  }
  else { const err = await res.json(); alert(err.detail || "Gagal pairing"); }
};

// INIT (Proteksi penuh)
(async () => {
  try {
    await loadMe();
    await loadFarms(); 
    await loadDevices(); 
    
    if (farmsCache.length > 0) {
      await loadAnalytics(farmsCache[0].id);
      await loadCharts(farmsCache[0].id);
    }
  } catch (err) {
    console.error("Terjadi kesalahan saat memuat dashboard:", err);
  }
})();