const apiBase = window.location.origin;

const healthBadge = document.getElementById("healthBadge");
const orderForm = document.getElementById("orderForm");
const etaForm = document.getElementById("etaForm");
const orderResult = document.getElementById("orderResult");
const etaResult = document.getElementById("etaResult");
const orderIdInput = document.getElementById("orderIdInput");
const ordersTableBody = document.getElementById("ordersTableBody");

const kpiTotalOrders = document.getElementById("kpiTotalOrders");
const kpiActiveTrucks = document.getElementById("kpiActiveTrucks");
const kpiAvgEta = document.getElementById("kpiAvgEta");
const kpiOnTime = document.getElementById("kpiOnTime");

const btnRefreshMap = document.getElementById("btnRefreshMap");
const btnRefreshActivity = document.getElementById("btnRefreshActivity");
const btnRefreshTable = document.getElementById("btnRefreshTable");

const map = L.map("map", { zoomControl: false }).setView([4.711, -74.0721], 11);
L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const markersLayer = L.layerGroup().addTo(map);

const chartCtx = document.getElementById("activityChart");
const activityChart = new Chart(chartCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Total",
        data: [],
        borderColor: "#35a9ff",
        backgroundColor: "#35a9ff22",
        fill: true,
        tension: 0.35,
        pointRadius: 3,
      },
      {
        label: "Delivered",
        data: [],
        borderColor: "#00d1b2",
        backgroundColor: "#00d1b222",
        fill: false,
        tension: 0.35,
        pointRadius: 3,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: "#cfe4ff" },
      },
    },
    scales: {
      x: { ticks: { color: "#9bb4d3" }, grid: { color: "#1f3550" } },
      y: { ticks: { color: "#9bb4d3" }, grid: { color: "#1f3550" } },
    },
  },
});

function formatNumber(value) {
  return new Intl.NumberFormat("es-CO").format(value);
}

function formatDateTime(iso) {
  try {
    return new Date(iso).toLocaleString("es-CO", { hour12: false });
  } catch (_err) {
    return iso;
  }
}

function prettyJson(obj) {
  return JSON.stringify(obj, null, 2);
}

function statusClass(status) {
  if (status === "delivered") return "status-delivered";
  if (status === "assigned") return "status-assigned";
  return "status-pending";
}

function markerColor(status) {
  if (status === "delivered") return "#00d1b2";
  if (status === "assigned") return "#35a9ff";
  return "#f4b942";
}

async function fetchJson(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} - ${await response.text()}`);
  }
  return response.json();
}

async function checkHealth() {
  try {
    const data = await fetchJson("/health");
    healthBadge.textContent = `API: ${data.status} (${data.env})`;
    healthBadge.style.color = "#71ffd6";
    healthBadge.style.borderColor = "#17644f";
  } catch (_error) {
    healthBadge.textContent = "API: down";
    healthBadge.style.color = "#ffb1a9";
    healthBadge.style.borderColor = "#6f3027";
  }
}

async function loadSummary() {
  const data = await fetchJson("/dashboard/summary");
  kpiTotalOrders.textContent = formatNumber(data.total_orders || 0);
  kpiActiveTrucks.textContent = formatNumber(data.active_trucks || 0);
  kpiAvgEta.textContent = data.avg_eta_minutes == null ? "No data" : `${data.avg_eta_minutes} min`;
  kpiOnTime.textContent = `${data.on_time_rate ?? 0}%`;
}

async function loadActivity() {
  const data = await fetchJson("/dashboard/activity?days=7");
  const series = data.series || [];
  activityChart.data.labels = series.map((item) => item.date.slice(5));
  activityChart.data.datasets[0].data = series.map((item) => item.total);
  activityChart.data.datasets[1].data = series.map((item) => item.delivered);
  activityChart.update();
}

function updateMap(orders) {
  markersLayer.clearLayers();
  const points = [];

  orders.forEach((order) => {
    const lat = Number(order.destination.lat);
    const lng = Number(order.destination.lng);

    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      return;
    }

    const marker = L.circleMarker([lat, lng], {
      radius: 7,
      weight: 2,
      color: markerColor(order.status),
      fillColor: markerColor(order.status),
      fillOpacity: 0.85,
    });

    marker.bindPopup(
      `<b>Order #${order.id}</b><br/>Status: ${order.status}<br/>Weight: ${order.weight_kg} kg` +
        `<br/>ETA: ${order.eta_minutes == null ? "N/A" : `${order.eta_minutes.toFixed(1)} min`}`
    );

    marker.addTo(markersLayer);
    points.push([lat, lng]);
  });

  if (points.length > 0) {
    map.fitBounds(points, { padding: [25, 25], maxZoom: 13 });
  }
}

function updateTable(orders) {
  if (!orders.length) {
    ordersTableBody.innerHTML =
      '<tr><td colspan="6" style="text-align:center;color:#8ea7c5;">No orders available.</td></tr>';
    return;
  }

  const rows = orders.map((order) => {
    const eta = order.eta_minutes == null ? "N/A" : `${order.eta_minutes.toFixed(1)} min`;
    const risk = order.late_risk == null ? "N/A" : order.late_risk.toFixed(2);

    return `
      <tr>
        <td>${order.id}</td>
        <td><span class="status-pill ${statusClass(order.status)}">${order.status}</span></td>
        <td>${formatDateTime(order.created_at)}</td>
        <td>${order.weight_kg}</td>
        <td>${eta}</td>
        <td>${risk}</td>
      </tr>
    `;
  });

  ordersTableBody.innerHTML = rows.join("");
}

async function loadRecentOrders() {
  const data = await fetchJson("/dashboard/recent-orders?limit=40");
  const orders = data.orders || [];
  updateMap(orders);
  updateTable(orders);
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

  orderResult.textContent = "Creating order...";
  try {
    const response = await fetch(`${apiBase}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();
    orderIdInput.value = data.id;
    orderResult.textContent = prettyJson(data);

    await Promise.all([loadSummary(), loadRecentOrders()]);
  } catch (error) {
    orderResult.textContent = `Error creating order: ${String(error.message || error)}`;
  }
});

etaForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(etaForm);
  const orderId = Number(form.get("order_id"));

  if (!orderId) {
    etaResult.textContent = "Invalid order id.";
    return;
  }

  etaResult.textContent = "Calculating ETA...";
  try {
    const data = await fetchJson(`/orders/${orderId}/eta`);
    etaResult.textContent = prettyJson(data);
    await Promise.all([loadSummary(), loadRecentOrders()]);
  } catch (error) {
    etaResult.textContent = `Error fetching ETA: ${String(error.message || error)}`;
  }
});

btnRefreshMap.addEventListener("click", () => {
  loadRecentOrders().catch((error) => {
    console.error(error);
  });
});

btnRefreshTable.addEventListener("click", () => {
  loadRecentOrders().catch((error) => {
    console.error(error);
  });
});

btnRefreshActivity.addEventListener("click", () => {
  loadActivity().catch((error) => {
    console.error(error);
  });
});

async function refreshAll() {
  await checkHealth();
  await Promise.all([loadSummary(), loadActivity(), loadRecentOrders()]);
}

refreshAll().catch((error) => {
  console.error(error);
});

setInterval(() => {
  refreshAll().catch((error) => {
    console.error(error);
  });
}, 45000);
