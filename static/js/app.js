/**
 * Main app JS — Session 1
 * - Initializes Leaflet map on the index page
 * - Seed / clear-seed button handlers
 * - Save toggle
 * - Toast notification helper
 */

/* =====================================================================
   Toast
   ===================================================================== */
function showToast(message, type = "info", durationMs = 3500) {
  const toast = document.getElementById("toast");
  const inner = document.getElementById("toast-inner");
  if (!toast || !inner) return;

  inner.textContent = message;
  inner.className = "";
  inner.classList.add(
    "px-4", "py-3", "rounded-lg", "shadow-lg", "text-sm", "font-medium", "text-white", "max-w-sm",
    type === "success" ? "toast-success" : type === "error" ? "toast-error" : "toast-info"
  );

  toast.classList.remove("hidden", "hide");
  toast.classList.add("show");

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.classList.add("hide");
    setTimeout(() => {
      toast.classList.remove("show", "hide");
      toast.classList.add("hidden");
    }, 300);
  }, durationMs);
}

/* =====================================================================
   Seed data
   ===================================================================== */
async function seedData() {
  const btn = document.getElementById("seed-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Seeding...";
  }
  try {
    const res = await fetch("/api/seed", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast("Error: " + data.message, "error");
      if (btn) { btn.disabled = false; btn.textContent = "Seed Sample Data"; }
    }
  } catch (err) {
    showToast("Request failed. Is the server running?", "error");
    if (btn) { btn.disabled = false; btn.textContent = "Seed Sample Data"; }
  }
}

async function scrapeQasa() {
  const btn = document.getElementById("scrape-btn");
  const text = document.getElementById("scrape-btn-text");
  const icon = document.getElementById("scrape-icon");
  const spinner = document.getElementById("scrape-spinner");

  if (btn) btn.disabled = true;
  if (text) text.textContent = "Scraping…";
  if (icon) icon.classList.add("hidden");
  if (spinner) spinner.classList.remove("hidden");

  showToast("Scraping Qasa listings — this may take a few minutes…", "info", 10000);

  try {
    const res = await fetch("/scrape", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      const msg = `Found ${data.new} new listing${data.new !== 1 ? "s" : ""}` +
        (data.duplicates ? `, ${data.duplicates} duplicate${data.duplicates !== 1 ? "s" : ""} skipped` : "") +
        (data.errors ? `, ${data.errors} error${data.errors !== 1 ? "s" : ""}` : "") + ".";
      showToast(msg, data.new > 0 ? "success" : "info", 5000);
      if (data.new > 0) setTimeout(() => window.location.reload(), 1200);
    } else {
      showToast("Scrape failed: " + (data.error || "unknown error"), "error");
    }
  } catch (err) {
    showToast("Scrape request failed. Is the server running?", "error");
  } finally {
    if (btn) btn.disabled = false;
    if (text) text.textContent = "Refresh Listings";
    if (icon) icon.classList.remove("hidden");
    if (spinner) spinner.classList.add("hidden");
  }
}

async function clearSeedData() {
  if (!confirm("Remove all seed listings? This cannot be undone.")) return;
  try {
    const res = await fetch("/api/clear-seed", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast("Error: " + data.message, "error");
    }
  } catch (err) {
    showToast("Request failed.", "error");
  }
}

/* =====================================================================
   Save toggle
   ===================================================================== */
async function toggleSave(listingId, btn) {
  try {
    const res = await fetch(`/listings/${listingId}/save`, { method: "POST" });
    const data = await res.json();
    const svg = btn.querySelector("svg");
    if (data.is_saved) {
      btn.classList.add("text-yellow-400");
      btn.classList.remove("text-gray-300", "dark:text-gray-600");
      if (svg) svg.setAttribute("fill", "currentColor");
      showToast("Listing saved.", "success", 2000);
    } else {
      btn.classList.remove("text-yellow-400");
      btn.classList.add("text-gray-300");
      if (svg) svg.setAttribute("fill", "none");
      showToast("Listing unsaved.", "info", 2000);
    }
  } catch (err) {
    showToast("Could not toggle save.", "error");
  }
}

/* =====================================================================
   Leaflet Map
   ===================================================================== */
function initMap() {
  const mapEl = document.getElementById("map");
  if (!mapEl || typeof L === "undefined") return;

  // Stockholm center
  const STOCKHOLM = [59.3293, 18.0686];

  const map = L.map("map", {
    center: STOCKHOLM,
    zoom: 11,
    zoomControl: true,
  });

  // Tile layer — OpenStreetMap
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // Add markers for listings that have coordinates
  const listings = window.LISTINGS_DATA || [];
  const bounds = [];

  listings.forEach((listing) => {
    if (!listing.lat || !listing.lng) return;

    const color = scoreColor(listing.ai_score);
    const markerHtml = `<div style="
      width: 14px; height: 14px; border-radius: 50%;
      background: ${color}; border: 2px solid white;
      box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    "></div>`;

    const icon = L.divIcon({
      html: markerHtml,
      className: "",
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });

    const marker = L.marker([listing.lat, listing.lng], { icon })
      .addTo(map)
      .bindPopup(buildPopup(listing));

    bounds.push([listing.lat, listing.lng]);
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }
}

function scoreColor(score) {
  if (score === null || score === undefined) return "#9ca3af";
  if (score >= 70) return "#16a34a";
  if (score >= 40) return "#ca8a04";
  return "#dc2626";
}

function buildPopup(listing) {
  const price = listing.price_sek
    ? listing.price_sek.toLocaleString("sv-SE") + " kr/mo"
    : "–";
  const rooms = listing.rooms ? listing.rooms + " rum" : "–";
  const district = listing.district || "";
  const score = listing.ai_score !== null && listing.ai_score !== undefined
    ? `<span style="color:${scoreColor(listing.ai_score)}; font-weight:600;">AI ${listing.ai_score}</span>`
    : "<span style='color:#9ca3af'>Not scored</span>";
  return `
    <div style="font-size:13px; min-width:160px;">
      <div style="font-weight:600; margin-bottom:4px;">${listing.title || "Listing"}</div>
      <div style="color:#6b7280; margin-bottom:4px;">${district}</div>
      <div>${price} &middot; ${rooms}</div>
      <div style="margin-top:4px;">${score}</div>
    </div>
  `;
}

/* =====================================================================
   Init
   ===================================================================== */
document.addEventListener("DOMContentLoaded", function () {
  initMap();
});
