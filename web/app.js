const apiBase = window.location.origin;

const healthBadge = document.getElementById("healthBadge");
const orderForm = document.getElementById("orderForm");
const etaForm = document.getElementById("etaForm");
const orderResult = document.getElementById("orderResult");
const etaResult = document.getElementById("etaResult");
const orderIdInput = document.getElementById("orderIdInput");

function prettyJson(obj) {
  return JSON.stringify(obj, null, 2);
}

async function checkHealth() {
  try {
    const res = await fetch(`${apiBase}/health`);
    if (!res.ok) throw new Error("health not ok");
    const data = await res.json();
    healthBadge.textContent = `API: ${data.status} (${data.env})`;
    healthBadge.style.borderColor = "#13b9cc";
    healthBadge.style.background = "#e8fcff";
  } catch (_error) {
    healthBadge.textContent = "API: no disponible";
    healthBadge.style.borderColor = "#f47a20";
    healthBadge.style.background = "#fff0e4";
  }
}

function nowIso() {
  return new Date().toISOString();
}

function plusHoursIso(hours) {
  const t = new Date();
  t.setHours(t.getHours() + hours);
  return t.toISOString();
}

orderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(orderForm);

  const payload = {
    created_at: nowIso(),
    promised_at: plusHoursIso(4),
    origin_lat: Number(form.get("origin_lat")),
    origin_lng: Number(form.get("origin_lng")),
    dest_lat: Number(form.get("dest_lat")),
    dest_lng: Number(form.get("dest_lng")),
    weight_kg: Number(form.get("weight_kg")),
    status: "pending",
  };

  orderResult.textContent = "Creando orden...";
  try {
    const res = await fetch(`${apiBase}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    orderIdInput.value = data.id;
    orderResult.textContent = `Orden creada: ${prettyJson(data)}`;
  } catch (error) {
    orderResult.textContent = `Error al crear orden: ${String(error.message || error)}`;
  }
});

etaForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(etaForm);
  const orderId = Number(form.get("order_id"));
  if (!orderId) {
    etaResult.textContent = "Debes ingresar un order_id valido.";
    return;
  }

  etaResult.textContent = "Consultando ETA...";
  try {
    const res = await fetch(`${apiBase}/orders/${orderId}/eta`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    etaResult.textContent = `Prediccion: ${prettyJson(data)}`;
  } catch (error) {
    etaResult.textContent = `Error consultando ETA: ${String(error.message || error)}`;
  }
});

checkHealth();
setInterval(checkHealth, 30000);
