const urlParams = new URLSearchParams(window.location.search);
const deviceId = urlParams.get('id');
if (!deviceId) window.location.href = "/dashboard.html";

const token = localStorage.getItem("token");
if (!token) window.location.href = "/login.html";
const headers = { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" };
const msg = document.getElementById("msg");

async function api(path, opts = {}) {
  const res = await fetch(`/api/v1${path}`, { ...opts, headers: { ...headers, ...(opts.headers || {}) } });
  if (res.status === 401) { localStorage.removeItem("token"); window.location.href = "/login.html"; return null; }
  return res;
}

function openModal(id) { document.getElementById(id).classList.add("active"); }
function closeModals() { document.querySelectorAll(".modal-overlay").forEach(el => el.classList.remove("active")); }
document.querySelectorAll(".btn-close-modal").forEach(btn => btn.onclick = closeModals);

function formatWIB(dateString) {
  if (!dateString) return "Belum";
  const date = new Date(dateString + "Z");
  // Gunakan format waktu lokal agar 02:50 WIB tampil sebagai 02:50
  return date.toLocaleString('id-ID', { hour12: false }).replace(/\//g, '/');
}

async function loadDevice() {
  const res = await api(`/devices/${deviceId}`);
  if (!res || !res.ok) { alert("Alat tidak ditemukan"); window.location.href = "/dashboard.html"; return; }
  const d = await res.json();
  
  document.getElementById("device-title").textContent = d.name || "Detail Alat";
  document.getElementById("dev-serial").textContent = d.serial;
  
  const statusEl = document.getElementById("dev-status");
  const dotEl = document.getElementById("dev-dot");
  statusEl.textContent = d.status.toUpperCase();
  
  if(d.status === 'online') {
    statusEl.style.color = "var(--green)";
    dotEl.className = "dot online";
  } else {
    statusEl.style.color = "var(--text-muted)";
    dotEl.className = "dot offline";
  }
  
  document.getElementById("dev-last-seen").textContent = formatWIB(d.last_seen_at);
  document.getElementById("inp-new-name").value = d.name || d.serial;
}

async function loadLogs() {
  const devRes = await api(`/devices/${deviceId}`);
  if (!devRes) return;
  const device = await devRes.json();
  const res = await api(`/farms/${device.farm_id}/logs`);
  if (!res) return;
  const data = await res.json();
  const el = document.getElementById("logs");
  if (!data.length) { el.innerHTML = `<p class="muted">Belum ada riwayat.</p>`; return; }
  
  const deviceLogs = data.filter(l => l.device_id === deviceId);
  if (!deviceLogs.length) { el.innerHTML = `<p class="muted">Belum ada riwayat untuk alat ini.</p>`; return; }

  el.innerHTML = deviceLogs.map(l => `
    <div class="list-item">
      <div>
        <div class="item-title"><i class="fa-solid ${l.event_type === 'manual_feed' ? 'fa-hand' : 'fa-clock'}" style="color: var(--cyan);"></i> ${l.event_type === 'manual_feed' ? 'Manual' : 'Jadwal'}</div>
        <div class="item-sub">${formatWIB(l.event_at)}</div>
      </div>
      <span class="badge ok">${l.amount_kg ? l.amount_kg + ' kg' : '-'}</span>
    </div>`).join("");
}

async function loadSchedules() {
  const res = await api(`/devices/${deviceId}/schedules`);
  if (!res) return;
  const data = await res.json();
  const el = document.getElementById("schedules");
  if (!data.length) { el.innerHTML = `<p class="muted">Belum ada jadwal.</p>`; return; }
  
  el.innerHTML = data.map(s => `
    <div class="list-item" style="opacity: ${s.is_enabled ? 1 : 0.5};">
      <div>
        <div class="item-title" style="font-size: 1.2rem;">${String(s.hour).padStart(2, '0')}:${String(s.minute).padStart(2, '0')}</div>
        <div class="item-sub">M: ${s.motor_duration_sec}s | B: ${s.blower_duration_sec}s</div>
      </div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <label class="toggle" style="position:relative; display:inline-block; width:46px; height:26px;">
          <input type="checkbox" ${s.is_enabled ? 'checked' : ''} onchange="toggleJadwal('${s.id}', this.checked)" style="opacity:0; width:0; height:0;">
          <span class="slider" style="position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background-color:#334155; transition:.4s; border-radius:26px;"></span>
        </label>
        <button onclick="hapusJadwal('${s.id}')" style="background:none; border:none; color: var(--red); font-size: 1rem;"><i class="fa-solid fa-trash"></i></button>
      </div>
    </div>`).join("");
}
const style = document.createElement('style');
style.innerHTML = `input:checked + .slider { background: linear-gradient(135deg, var(--cyan), var(--blue)) !important; box-shadow: 0 0 10px rgba(6,182,212,0.4); } .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; } input:checked + .slider:before { transform: translateX(20px); }`;
document.head.appendChild(style);

document.getElementById("btn-feed").onclick = async () => {
  msg.textContent = "Mengirim...";
  const res = await api(`/devices/${deviceId}/feed`, { method: "POST" });
  if (res && res.ok) {
    msg.textContent = "✅ Pakan diberikan.";
    await loadDevice(); await loadLogs();
  } else {
    const err = await res.json();
    msg.textContent = err.detail || "Gagal";
    msg.style.color = "var(--red)";
  }
};

document.getElementById("btn-online").onclick = async () => {
  const res = await api(`/devices/${deviceId}/simulate-heartbeat`, { method: "POST" });
  if (res && res.ok) { msg.textContent = "✅ Alat Online."; await loadDevice(); }
};

document.getElementById("form-schedule").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    hour: parseInt(document.getElementById("sch-hour").value),
    minute: parseInt(document.getElementById("sch-minute").value),
    motor_duration_sec: parseInt(document.getElementById("sch-motor").value),
    blower_duration_sec: parseInt(document.getElementById("sch-blower").value),
  };
  const res = await api(`/devices/${deviceId}/schedules`, { method: "POST", body: JSON.stringify(body) });
  if (res && res.ok) { await loadSchedules(); msg.textContent = "✅ Ditambahkan."; }
});

window.toggleJadwal = async (id, isChecked) => {
  await api(`/schedules/${id}`, { method: "PATCH", body: JSON.stringify({ is_enabled: isChecked }) });
  await loadSchedules();
};

window.hapusJadwal = async (id) => {
  if (!confirm("Hapus jadwal ini?")) return;
  await api(`/schedules/${id}`, { method: "DELETE" });
  await loadSchedules();
};

document.getElementById("btn-edit-name").onclick = () => openModal("modal-name");
document.getElementById("btn-save-name").onclick = async () => {
  const newName = document.getElementById("inp-new-name").value;
  if (!newName) return;
  const res = await api(`/devices/${deviceId}`, { method: "PATCH", body: JSON.stringify({ name: newName }) });
  if (res && res.ok) { closeModals(); await loadDevice(); }
};

document.getElementById("btn-unpair").onclick = async () => {
  if (!confirm("Yakin ingin melepas alat?")) return;
  const res = await api(`/devices/${deviceId}/unpair`, { method: "POST" });
  if (res && res.ok) { alert("Alat dilepas."); window.location.href = "/dashboard.html"; }
};

(async () => {
  await loadDevice();
  await loadLogs();
  await loadSchedules();
})();