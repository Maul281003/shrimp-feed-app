const form = document.getElementById("login-form");
const msg = document.getElementById("msg");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  msg.textContent = "";
  const body = {
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value,
  };
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json();
    msg.textContent = err.detail || "Login gagal";
    msg.className = "msg error";
    return;
  }
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  window.location.href = "/dashboard.html";
});