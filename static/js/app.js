/**
 * Stockholm Apartment Finder — Main App JS (Session 5)
 *
 * Sections:
 *  1. Toast
 *  2. Seed / Scrape / Save (data actions)
 *  3. Notes + Status (inline saves)
 *  4. Gallery navigation
 *  5. Description toggle
 *  6. Card expand / collapse
 *  7. Filter state + apply
 *  8. Leaflet map (init, markers, cluster, overlays)
 *  9. Init (DOMContentLoaded)
 */

/* =====================================================================
   1. TOAST
   ===================================================================== */
function showToast(message, type = "info", durationMs = 3500) {
  const toast = document.getElementById("toast");
  const inner = document.getElementById("toast-inner");
  if (!toast || !inner) return;

  inner.textContent = message;
  inner.className = "px-4 py-3 rounded-lg shadow-lg text-sm font-medium text-white max-w-sm " +
    (type === "success" ? "toast-success" : type === "error" ? "toast-error" : "toast-info");

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
   2. SEED / SCRAPE / SAVE
   ===================================================================== */
async function seedData() {
  const btn = document.getElementById("seed-btn");
  if (btn) { btn.disabled = true; btn.textContent = "Seeding…"; }
  try {
    const res = await fetch("/api/seed", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast("Error: " + data.message, "error");
      if (btn) { btn.disabled = false; btn.textContent = "Seed"; }
    }
  } catch {
    showToast("Request failed.", "error");
    if (btn) { btn.disabled = false; btn.textContent = "Seed"; }
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
  } catch {
    showToast("Request failed.", "error");
  }
}

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
    // Update data attribute for filter
    const wrapper = document.querySelector(`[data-listing-id="${listingId}"]`);
    if (wrapper) wrapper.dataset.saved = data.is_saved ? "true" : "false";
  } catch {
    showToast("Could not toggle save.", "error");
  }
}

/* =====================================================================
   3. NOTES + STATUS (inline saves)
   ===================================================================== */
async function saveNotes(listingId, value) {
  try {
    await fetch(`/listings/${listingId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: value }),
    });
    showToast("Notes saved.", "success", 1500);
  } catch {
    showToast("Could not save notes.", "error");
  }
}

async function updateStatus(listingId, status) {
  try {
    const res = await fetch(`/listings/${listingId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ application_status: status }),
    });
    const data = await res.json();
    if (res.ok) {
      // Update data attribute for filter
      const wrapper = document.querySelector(`[data-listing-id="${listingId}"]`);
      if (wrapper) wrapper.dataset.status = status;

      // Update the status badge below the thumbnail
      const badge = wrapper && wrapper.querySelector(".status-thumb-badge");
      if (badge) {
        const base = "status-thumb-badge text-[10px] px-1.5 py-0.5 rounded-full font-medium capitalize w-20 text-center truncate";
        const colorMap = {
          accepted: "bg-green-100 text-green-700",
          rejected: "bg-red-100 text-red-600",
          waiting: "bg-purple-100 text-purple-700",
          applied: "bg-blue-100 text-blue-700",
        };
        if (status === "not_applied") {
          badge.className = base + " hidden";
        } else {
          badge.className = base + " " + (colorMap[status] || colorMap.applied);
          badge.textContent = status.replace("_", " ");
        }
      }

      showToast("Status updated.", "success", 1500);
    } else {
      showToast("Could not update status: " + (data.error || ""), "error");
    }
  } catch {
    showToast("Could not update status.", "error");
  }
}

async function deleteListing(listingId) {
  if (!confirm("Permanently delete this listing? This cannot be undone.")) return;
  try {
    const res = await fetch(`/listings/${listingId}/delete`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.success) {
      // Remove card from DOM
      const wrapper = document.querySelector(`[data-listing-id="${listingId}"]`);
      if (wrapper) wrapper.remove();
      // Remove marker from map
      const marker = window._markerById && window._markerById[listingId];
      if (marker) {
        if (window._clusterGroup) window._clusterGroup.removeLayer(marker);
        else if (window._map) window._map.removeLayer(marker);
        delete window._markerById[listingId];
      }
      delete (window._listingById || {})[listingId];
      clearMapOverlays();
      // Update listing count
      const countEl = document.getElementById("listings-count");
      if (countEl) {
        const remaining = document.querySelectorAll(".listing-card-wrapper").length;
        countEl.textContent = `(${remaining})`;
      }
      showToast("Listing deleted.", "success", 2000);
    } else {
      showToast("Delete failed: " + (data.error || "unknown error"), "error");
    }
  } catch {
    showToast("Delete request failed.", "error");
  }
}

async function reScrap(listingId, url) {
  const btn = document.getElementById(`rescrap-btn-${listingId}`);
  const originalText = btn.innerHTML;

  if (btn) btn.disabled = true;
  btn.innerHTML = '<svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg> Re-scraping…';
  showToast("Re-scraping listing…", "info", 10000);

  try {
    const res = await fetch("/listings/bulk-import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls: [url] }),
    });
    const data = await res.json();
    if (res.ok && data.results && data.results.length > 0) {
      const result = data.results[0];
      if (result.status === "updated") {
        showToast("Listing updated with latest data!", "success", 3000);
        setTimeout(() => window.location.reload(), 1500);
      } else if (result.status === "saved") {
        showToast("Listing saved!", "success", 3000);
        setTimeout(() => window.location.reload(), 1500);
      } else {
        showToast("Re-scrap failed: " + (result.error || "unknown error"), "error");
      }
    } else {
      showToast("Re-scrap failed: " + (data.error || "unknown error"), "error");
    }
  } catch {
    showToast("Re-scrap request failed. Is the server running?", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}

async function reEnrich(listingId) {
  const btn = document.getElementById(`reenrich-btn-${listingId}`);
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Fetching data…";
  }
  try {
    const res = await fetch(`/api/enrich/${listingId}`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.success) {
      const e = data.enriched || {};
      const parts = [];
      if (e.geocoded) parts.push("location");
      if (e.commute) parts.push("commute");
      if (e.route) parts.push("transit route");
      if (e.stops) parts.push("nearby stops");
      if (e.pois) parts.push("POIs");
      showToast(parts.length ? `Updated: ${parts.join(", ")}.` : "Already up to date.", "success");
      // Reload page so all template sections (commute, stops, POIs) re-render with new data
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast("Re-enrich failed: " + (data.error || "unknown error"), "error");
      if (btn) { btn.disabled = false; btn.innerHTML = `<svg class="w-3.5 h-3.5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>Re-enrich`; }
    }
  } catch {
    showToast("Re-enrich request failed.", "error");
    if (btn) { btn.disabled = false; btn.textContent = "Re-enrich"; }
  }
}

/* =====================================================================
   4. THUMBNAIL SCROLL + MAP FOCUS HELPERS
   ===================================================================== */
function scrollThumb(listingId, dir) {
  const row = document.getElementById(`thumbrow-${listingId}`);
  if (!row) return;
  row.scrollBy({ left: dir * 90, behavior: "smooth" });
}

function focusMapOnListing(listingId) {
  const listing = (window._listingById || {})[listingId];
  if (!listing) return;
  focusListingOnMap(listing);
}

/* =====================================================================
   5. LIGHTBOX
   ===================================================================== */
window._lbImages = [];
window._lbIdx = 0;

function openLightbox(listingId, startIdx) {
  const listing = (window._listingById || {})[listingId];
  if (!listing || !listing.images || !listing.images.length) return;
  window._lbImages = listing.images;
  window._lbIdx = startIdx || 0;
  _lbRender();
  const lb = document.getElementById("lightbox");
  if (lb) { lb.classList.remove("hidden"); lb.classList.add("flex"); }
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  const lb = document.getElementById("lightbox");
  if (lb) { lb.classList.add("hidden"); lb.classList.remove("flex"); }
  document.body.style.overflow = "";
}

function lightboxNext() {
  window._lbIdx = (window._lbIdx + 1) % window._lbImages.length;
  _lbRender();
}

function lightboxPrev() {
  window._lbIdx = (window._lbIdx - 1 + window._lbImages.length) % window._lbImages.length;
  _lbRender();
}

function _lbRender() {
  const img = document.getElementById("lightbox-img");
  const counter = document.getElementById("lightbox-counter");
  if (img) img.src = window._lbImages[window._lbIdx] || "";
  if (counter) counter.textContent = `${window._lbIdx + 1} / ${window._lbImages.length}`;
}

/* =====================================================================
   6. DESCRIPTION TOGGLE
   ===================================================================== */
function toggleDesc(listingId) {
  const el = document.getElementById(`desc-${listingId}`);
  const btn = document.getElementById(`desc-btn-${listingId}`);
  if (!el) return;
  const expanded = el.style.webkitLineClamp === "unset" || el.style.overflow === "visible";
  if (expanded) {
    el.style.display = "-webkit-box";
    el.style.webkitLineClamp = "5";
    el.style.webkitBoxOrient = "vertical";
    el.style.overflow = "hidden";
    if (btn) btn.textContent = "Show more";
  } else {
    el.style.display = "block";
    el.style.webkitLineClamp = "unset";
    el.style.overflow = "visible";
    if (btn) btn.textContent = "Show less";
  }
}

/* =====================================================================
   7. CARD EXPAND / COLLAPSE
   ===================================================================== */
window._expandedCardId = null;

function toggleCard(listingId) {
  if (window._expandedCardId === listingId) {
    collapseCard(listingId);
  } else {
    if (window._expandedCardId !== null) {
      collapseCard(window._expandedCardId);
    }
    expandCard(listingId);
  }
}

function expandCard(listingId, focusMap = false) {
  const detail = document.getElementById(`detail-${listingId}`);
  const wrapper = document.querySelector(`[data-listing-id="${listingId}"]`);
  if (!detail) return;

  detail.classList.remove("hidden");
  window._expandedCardId = listingId;

  // Visual highlight
  document.querySelectorAll(".listing-card-wrapper").forEach(c =>
    c.classList.remove("card-expanded")
  );
  if (wrapper) wrapper.classList.add("card-expanded");

  // Scroll card into view
  if (wrapper) wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });

  // Map: zoom only if triggered from map; otherwise just open popup label
  const listing = (window._listingById || {})[listingId];
  if (listing) {
    if (focusMap) {
      focusListingOnMap(listing);
    } else {
      const marker = window._markerById[listingId];
      if (marker) marker.openPopup();
    }
    showMapOverlays(listing);
  }
}

function collapseCard(listingId) {
  const detail = document.getElementById(`detail-${listingId}`);
  const wrapper = document.querySelector(`[data-listing-id="${listingId}"]`);
  if (detail) detail.classList.add("hidden");
  if (wrapper) wrapper.classList.remove("card-expanded");
  if (window._expandedCardId === listingId) window._expandedCardId = null;
  clearMapOverlays();
  // Close the marker popup
  const marker = window._markerById && window._markerById[listingId];
  if (marker && window._map) window._map.closePopup();
}

/* =====================================================================
   7. FILTER STATE + APPLY
   ===================================================================== */
const _filterState = {
  sort: "newest",
  savedOnly: false,
  appliedOnly: false,
  minPrice: null,
  maxPrice: null,
  rooms: [],      // array of ints (selected room counts)
  maxCommute: 0,       // 0 = any
  districts: [],      // array of strings
  amenities: [],      // array of amenity keys
};

// Room filter toggle
function toggleRoomFilter(n) {
  const idx = _filterState.rooms.indexOf(n);
  const btn = document.querySelector(`.room-filter-btn[data-room="${n}"]`);
  if (idx >= 0) {
    _filterState.rooms.splice(idx, 1);
    if (btn) btn.classList.remove("active-filter-btn");
  } else {
    _filterState.rooms.push(n);
    if (btn) btn.classList.add("active-filter-btn");
  }
  applyFilters();
}

// District filter toggle
function toggleDistrictFilter(district) {
  const idx = _filterState.districts.indexOf(district);
  const btn = document.querySelector(`.district-filter-btn[data-district="${district}"]`);
  if (idx >= 0) {
    _filterState.districts.splice(idx, 1);
    if (btn) btn.classList.remove("active-filter-btn");
  } else {
    _filterState.districts.push(district);
    if (btn) btn.classList.add("active-filter-btn");
  }
  applyFilters();
}

function updateCommuteLabel(val) {
  const label = document.getElementById("commute-label");
  if (label) label.textContent = val == 0 ? "Any" : `${val} min`;
}

function toggleFilterPanel() {
  const panel = document.getElementById("filter-panel");
  const btn = document.getElementById("filter-toggle-btn");
  if (!panel) return;
  const isOpen = !panel.classList.contains("hidden");
  panel.classList.toggle("hidden", isOpen);
  if (btn) btn.classList.toggle("bg-gray-100", !isOpen);
  if (btn) btn.classList.toggle("dark:bg-gray-700", !isOpen);
}

function onFilterChange() {
  // Read current input values into _filterState
  const sort = document.getElementById("filter-sort");
  if (sort) _filterState.sort = sort.value;

  const saved = document.getElementById("filter-saved");
  if (saved) _filterState.savedOnly = saved.checked;

  const applied = document.getElementById("filter-applied");
  if (applied) _filterState.appliedOnly = applied.checked;

  const pMin = document.getElementById("filter-price-min");
  _filterState.minPrice = pMin && pMin.value ? parseInt(pMin.value) : null;

  const pMax = document.getElementById("filter-price-max");
  _filterState.maxPrice = pMax && pMax.value ? parseInt(pMax.value) : null;

  const commute = document.getElementById("filter-commute");
  _filterState.maxCommute = commute ? parseInt(commute.value) : 0;

  // Amenity checkboxes
  _filterState.amenities = [];
  document.querySelectorAll("[data-amenity]").forEach(cb => {
    if (cb.checked) _filterState.amenities.push(cb.dataset.amenity);
  });

  applyFilters();
}

function applyFilters() {
  const wrappers = document.querySelectorAll(".listing-card-wrapper");
  let visible = 0;

  // --- Sort ---
  sortCards(_filterState.sort);

  // --- Filter visibility ---
  wrappers.forEach(wrapper => {
    const id = parseInt(wrapper.dataset.listingId, 10);
    const listing = (window._listingById || {})[id];
    if (!listing) return;

    const price = parseInt(wrapper.dataset.price) || 0;
    const rooms = parseInt(wrapper.dataset.rooms) || 0;
    const commute = parseInt(wrapper.dataset.commute) || 9999;
    const district = wrapper.dataset.district || "";
    const saved = wrapper.dataset.saved === "true";
    const status = wrapper.dataset.status || "not_applied";
    const amenStr = wrapper.dataset.amenities || "";
    const amenList = amenStr ? amenStr.split(",") : [];

    let show = true;

    if (_filterState.savedOnly && !saved) show = false;
    if (_filterState.appliedOnly && status === "not_applied") show = false;
    if (_filterState.minPrice && price < _filterState.minPrice) show = false;
    if (_filterState.maxPrice && price > _filterState.maxPrice) show = false;
    if (_filterState.maxCommute > 0 && commute > _filterState.maxCommute) show = false;

    if (_filterState.rooms.length) {
      const match = _filterState.rooms.some(r => r === 4 ? rooms >= 4 : rooms === r);
      if (!match) show = false;
    }

    if (_filterState.districts.length) {
      if (!_filterState.districts.includes(district)) show = false;
    }

    if (_filterState.amenities.length) {
      const hasAll = _filterState.amenities.every(a =>
        amenList.includes(a) ||
        (a === "washing_machine" && listing.has_washing_machine) ||
        (a === "tumble_dryer" && listing.has_dryer) ||
        (a === "dishwasher" && listing.has_dishwasher)
      );
      if (!hasAll) show = false;
    }

    wrapper.classList.toggle("hidden", !show);
    if (show) visible++;
  });

  // Update count label
  const countEl = document.getElementById("listings-count");
  if (countEl) {
    const total = wrappers.length;
    countEl.textContent = visible === total ? `(${total})` : `(${visible} / ${total})`;
  }

  // Show "no results" empty state
  const noResults = document.getElementById("no-filter-results");
  const list = document.getElementById("listings-list");
  if (noResults) noResults.classList.toggle("hidden", visible > 0);
  if (list) list.classList.toggle("hidden", visible === 0);

  // Update filter badge count
  syncFilterCount();

  // Sync URL params
  syncUrlParams();

  // Update map (hide/show markers matching visible listings)
  updateMarkerVisibility();
}

function syncFilterCount() {
  const badge = document.getElementById("filter-count-badge");
  if (!badge) return;
  let count = 0;
  if (_filterState.minPrice) count++;
  if (_filterState.maxPrice) count++;
  if (_filterState.maxCommute > 0) count++;
  if (_filterState.rooms.length) count += _filterState.rooms.length;
  if (_filterState.districts.length) count += _filterState.districts.length;
  if (_filterState.amenities.length) count += _filterState.amenities.length;

  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
}

function resetFilters() {
  _filterState.sort = "newest";
  _filterState.savedOnly = false;
  _filterState.appliedOnly = false;
  _filterState.minPrice = null;
  _filterState.maxPrice = null;
  _filterState.rooms = [];
  _filterState.maxCommute = 0;
  _filterState.districts = [];
  _filterState.amenities = [];

  // Reset UI inputs
  const sort = document.getElementById("filter-sort");
  if (sort) sort.value = "newest";
  const saved = document.getElementById("filter-saved");
  if (saved) saved.checked = false;
  const applied = document.getElementById("filter-applied");
  if (applied) applied.checked = false;
  const pMin = document.getElementById("filter-price-min");
  if (pMin) pMin.value = "";
  const pMax = document.getElementById("filter-price-max");
  if (pMax) pMax.value = "";
  const commute = document.getElementById("filter-commute");
  if (commute) { commute.value = 0; updateCommuteLabel(0); }

  document.querySelectorAll(".room-filter-btn").forEach(b => b.classList.remove("active-filter-btn"));
  document.querySelectorAll(".district-filter-btn").forEach(b => b.classList.remove("active-filter-btn"));
  document.querySelectorAll("[data-amenity]").forEach(cb => cb.checked = false);

  applyFilters();
}

function sortCards(by) {
  const list = document.getElementById("listings-list");
  if (!list) return;
  const wrappers = Array.from(list.querySelectorAll(".listing-card-wrapper"));

  wrappers.sort((a, b) => {
    const la = (window._listingById || {})[parseInt(a.dataset.listingId)];
    const lb = (window._listingById || {})[parseInt(b.dataset.listingId)];
    if (!la || !lb) return 0;

    switch (by) {
      case "score":
        return (lb.ai_score ?? -1) - (la.ai_score ?? -1);
      case "price_asc":
        return (la.price_sek || 0) - (lb.price_sek || 0);
      case "price_desc":
        return (lb.price_sek || 0) - (la.price_sek || 0);
      case "commute":
        return (la.commute_minutes ?? 9999) - (lb.commute_minutes ?? 9999);
      case "newest":
      default:
        return new Date(lb.created_at || 0) - new Date(la.created_at || 0);
    }
  });

  wrappers.forEach(w => list.appendChild(w));
}

function syncUrlParams() {
  const p = new URLSearchParams();
  if (_filterState.sort !== "newest") p.set("sort", _filterState.sort);
  if (_filterState.savedOnly) p.set("saved", "1");
  if (_filterState.appliedOnly) p.set("applied", "1");
  if (_filterState.minPrice) p.set("min_price", _filterState.minPrice);
  if (_filterState.maxPrice) p.set("max_price", _filterState.maxPrice);
  if (_filterState.maxCommute > 0) p.set("commute", _filterState.maxCommute);
  if (_filterState.rooms.length) p.set("rooms", _filterState.rooms.join(","));
  if (_filterState.districts.length) p.set("districts", _filterState.districts.join(","));
  if (_filterState.amenities.length) p.set("amenities", _filterState.amenities.join(","));
  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
}

function readUrlParams() {
  const p = new URLSearchParams(window.location.search);
  if (p.get("sort")) _filterState.sort = p.get("sort");
  if (p.get("saved")) _filterState.savedOnly = true;
  if (p.get("applied")) _filterState.appliedOnly = true;
  if (p.get("min_price")) _filterState.minPrice = parseInt(p.get("min_price"));
  if (p.get("max_price")) _filterState.maxPrice = parseInt(p.get("max_price"));
  if (p.get("commute")) _filterState.maxCommute = parseInt(p.get("commute"));
  if (p.get("rooms")) _filterState.rooms = p.get("rooms").split(",").map(Number);
  if (p.get("districts")) _filterState.districts = p.get("districts").split(",");
  if (p.get("amenities")) _filterState.amenities = p.get("amenities").split(",");
}

function restoreFilterUI() {
  const sort = document.getElementById("filter-sort");
  if (sort) sort.value = _filterState.sort;
  const saved = document.getElementById("filter-saved");
  if (saved) saved.checked = _filterState.savedOnly;
  const applied = document.getElementById("filter-applied");
  if (applied) applied.checked = _filterState.appliedOnly;
  const pMin = document.getElementById("filter-price-min");
  if (pMin && _filterState.minPrice) pMin.value = _filterState.minPrice;
  const pMax = document.getElementById("filter-price-max");
  if (pMax && _filterState.maxPrice) pMax.value = _filterState.maxPrice;
  const commute = document.getElementById("filter-commute");
  if (commute) { commute.value = _filterState.maxCommute; updateCommuteLabel(_filterState.maxCommute); }

  _filterState.rooms.forEach(r => {
    const btn = document.querySelector(`.room-filter-btn[data-room="${r}"]`);
    if (btn) btn.classList.add("active-filter-btn");
  });
  _filterState.amenities.forEach(a => {
    const cb = document.querySelector(`[data-amenity="${a}"]`);
    if (cb) cb.checked = true;
  });
}

function initDistrictFilters() {
  const container = document.getElementById("district-filter-btns");
  if (!container) return;

  // Collect unique districts from listings data
  const districts = [...new Set(
    (window.LISTINGS_DATA || []).map(l => l.district).filter(Boolean)
  )].sort();

  districts.forEach(district => {
    const btn = document.createElement("button");
    btn.className = "district-filter-btn text-xs px-2.5 py-1 rounded border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-brand-400 transition-colors";
    btn.dataset.district = district;
    btn.textContent = district;
    btn.onclick = () => toggleDistrictFilter(district);
    if (_filterState.districts.includes(district)) {
      btn.classList.add("active-filter-btn");
    }
    container.appendChild(btn);
  });
}

/* =====================================================================
   8. AI LANGUAGE TOGGLE
   ===================================================================== */
window._aiLang = {}; // listingId → 'en' | 'tr'

function toggleAiLang(listingId) {
  const current = window._aiLang[listingId] || 'tr';
  const next = current === 'en' ? 'tr' : 'en';
  window._aiLang[listingId] = next;

  const label = next.toUpperCase();
  const headerToggle = document.getElementById(`ai-lang-toggle-${listingId}`);
  const detailToggle = document.getElementById(`ai-lang-toggle-detail-${listingId}`);
  if (headerToggle) headerToggle.textContent = label;
  if (detailToggle) detailToggle.textContent = label;

  const enContent = document.getElementById(`ai-content-en-${listingId}`);
  const trContent = document.getElementById(`ai-content-tr-${listingId}`);
  if (enContent) enContent.classList.toggle('hidden', next === 'tr');
  if (trContent) trContent.classList.toggle('hidden', next === 'en');
}

async function reScoreListing(listingId) {
  const btn = document.getElementById(`rescore-btn-${listingId}`);
  if (btn) { btn.disabled = true; btn.textContent = 'Scoring…'; }
  try {
    const resp = await fetch(`/api/score/${listingId}`, { method: 'POST' });
    const data = await resp.json();
    if (data.success && data.score != null) {
      showToast(`Re-scored: ${data.score}/100 — reloading…`, 'success', 3000);
      setTimeout(() => window.location.reload(), 800);
    } else {
      const msg = data.error || 'Re-scoring failed';
      if (btn) { btn.disabled = false; btn.textContent = 'Re-Score with AI'; }
      showToast(msg.includes('API_KEY') ? 'Add ANTHROPIC_API_KEY to .env to enable AI scoring' : msg, 'error');
    }
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = 'Re-Score with AI'; }
    showToast('Re-score request failed', 'error');
  }
}

/* =====================================================================
   9. LEAFLET MAP
   ===================================================================== */
window._map = null;
window._markerById = {};   // listingId → Leaflet marker
window._clusterGroup = null;
window._workMarker = null;
window._listingById = {};   // fast lookup: listingId → listing data
window._supermarketLayers = []; // supermarket markers shown on card expand
window._gymLayers = [];           // gym markers shown on card expand
window._parkLayers = [];          // park markers shown on card expand
window._routeLayers = []; // transit route polylines shown on card expand
window._showSupermarkets = false; // supermarket overlay toggle (default off)
window._showGyms = false;         // gym overlay toggle (default off)
window._showParks = false;        // park overlay toggle (default off)

/* Decode a Google Maps encoded polyline string → [[lat, lng], ...] */
function decodePolyline(str) {
  let index = 0, lat = 0, lng = 0, result = [];
  while (index < str.length) {
    let b, shift = 0, res = 0;
    do { b = str.charCodeAt(index++) - 63; res |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    lat += (res & 1) ? ~(res >> 1) : (res >> 1);
    shift = 0; res = 0;
    do { b = str.charCodeAt(index++) - 63; res |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    lng += (res & 1) ? ~(res >> 1) : (res >> 1);
    result.push([lat / 1e5, lng / 1e5]);
  }
  return result;
}

/* Return a Leaflet polyline color/dash style for a transit step */
function _routeStepStyle(step) {
  if (step.mode === "WALKING") return { color: "#6b7280", weight: 3, dashArray: "5, 7", opacity: 0.85 };
  const v = (step.vehicle || "").toUpperCase();
  if (v === "SUBWAY" || v === "METRO_RAIL" || v === "HEAVY_RAIL") return { color: "#2563eb", weight: 5, opacity: 0.9 };
  if (v === "TRAM" || v === "LIGHT_RAIL") return { color: "#7c3aed", weight: 5, opacity: 0.9 };
  if (v === "BUS") return { color: "#16a34a", weight: 4, opacity: 0.85 };
  if (v === "FERRY") return { color: "#0891b2", weight: 4, opacity: 0.85 };
  return { color: "#f59e0b", weight: 4, opacity: 0.85 };
}

function initMap() {
  const mapEl = document.getElementById("map");
  if (!mapEl || typeof L === "undefined") return;

  // Build fast lookup index
  (window.LISTINGS_DATA || []).forEach(l => {
    window._listingById[l.id] = l;
  });

  const STOCKHOLM = [59.3293, 18.0686];
  const map = L.map("map", { center: STOCKHOLM, zoom: 11, zoomControl: true });
  window._map = map;

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // Marker cluster group (optional — falls back to direct map layers)
  if (typeof L.markerClusterGroup === "function") {
    const cluster = L.markerClusterGroup({ maxClusterRadius: 50, disableClusteringAtZoom: 15 });
    window._clusterGroup = cluster;
    map.addLayer(cluster);
  }

  // Add listing markers
  const bounds = [];
  (window.LISTINGS_DATA || []).forEach(listing => {
    if (!listing.lat || !listing.lng) return;
    const marker = createListingMarker(listing);
    window._markerById[listing.id] = marker;
    if (window._clusterGroup) {
      window._clusterGroup.addLayer(marker);
    } else {
      marker.addTo(map);
    }
    bounds.push([listing.lat, listing.lng]);
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }

  // Work address marker
  const s = window.SETTINGS_DATA || {};
  if (s.work_lat && s.work_lng) {
    const workIcon = L.divIcon({
      html: `<div style="
        width:22px;height:22px;border-radius:50%;
        background:#7c3aed;border:3px solid white;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        display:flex;align-items:center;justify-content:center;
        font-size:11px;line-height:1;">★</div>`,
      className: "",
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });
    window._workMarker = L.marker([s.work_lat, s.work_lng], { icon: workIcon, zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup(`<div style="font-size:13px;font-weight:600;">Work</div><div style="font-size:12px;color:#6b7280;">${s.work_address || ""}</div>`);
  }

  // Clicking a map marker expands that card + zooms map
  Object.entries(window._markerById).forEach(([id, marker]) => {
    marker.on("click", () => {
      const intId = parseInt(id, 10);
      if (window._expandedCardId !== null && window._expandedCardId !== intId) {
        collapseCard(window._expandedCardId);
      }
      expandCard(intId, true);
    });
  });
}

function createListingMarker(listing) {
  const color = scoreColor(listing.ai_score);
  const icon = L.divIcon({
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3);"></div>`,
    className: "",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
  return L.marker([listing.lat, listing.lng], { icon }).bindPopup(buildPopup(listing));
}

function focusListingOnMap(listing) {
  const marker = window._markerById[listing.id];
  const map = window._map;
  if (!marker || !map) return;

  // If inside a cluster, spiderfy it first
  if (window._clusterGroup) {
    window._clusterGroup.zoomToShowLayer(marker, () => {
      map.setView(marker.getLatLng(), Math.max(map.getZoom(), 14), { animate: true });
      marker.openPopup();
    });
  } else {
    map.setView(marker.getLatLng(), 14, { animate: true });
    marker.openPopup();
  }
}

async function showMapOverlays(listing) {
  clearMapOverlays();
  const map = window._map;
  if (!map) return;

  // --- Transit route overlay ---
  if (listing.lat && listing.lng) {
    let routeData = null;
    // Prefer cached route from LISTINGS_DATA
    if (listing.transit_route && listing.transit_route.steps && listing.transit_route.steps.length) {
      routeData = listing.transit_route;
    } else {
      // Fallback: fetch via API (should only happen for listings without cached route)
      try {
        const resp = await fetch(`/api/transit-route/${listing.id}`);
        const data = await resp.json();
        if (data.success && data.steps && data.steps.length) {
          routeData = data;
        }
      } catch (_) { /* no route — silently skip */ }
    }

    if (routeData && routeData.steps) {
      routeData.steps.forEach(step => {
        const latlngs = decodePolyline(step.polyline);
        if (!latlngs.length) return;
        const style = _routeStepStyle(step);
        const line = L.polyline(latlngs, style).addTo(map);
        const label = step.mode === "TRANSIT"
          ? `<b>${step.line_name || step.vehicle}</b> ${step.departure_stop} → ${step.arrival_stop} (${step.duration_min} min)`
          : `Walk ${step.duration_min} min`;
        line.bindTooltip(label, { sticky: true, className: "route-tooltip" });
        window._routeLayers.push(line);
      });
      // Fit map to show full route
      const allPoints = window._routeLayers.flatMap(l => l.getLatLngs());
      if (allPoints.length) map.fitBounds(L.latLngBounds(allPoints), { padding: [40, 40], maxZoom: 15 });
      // Show route legend
      const legend = document.getElementById("route-legend");
      if (legend) legend.classList.remove("hidden");
    }
  }

  if (window._showSupermarkets) _showSupermarketMarkers(listing);
  if (window._showGyms) _showGymMarkers(listing);
  if (window._showParks) _showParkMarkers(listing);
}

function _showSupermarketMarkers(listing) {
  const map = window._map;
  if (!map) return;
  const supermarkets = (listing.nearby_pois || {}).supermarkets || [];
  supermarkets.forEach(poi => {
    if (!poi.lat || !poi.lng) return;

    const distText = poi.distance_m
      ? poi.distance_m < 1000
        ? `${poi.distance_m}m away`
        : `${(poi.distance_m / 1000).toFixed(1)}km away`
      : "";

    const icon = L.divIcon({
      html: `<div style="
        width:26px;height:26px;border-radius:50%;
        background:#0284c7;border:2.5px solid white;
        box-shadow:0 2px 6px rgba(0,0,0,0.35);
        display:flex;align-items:center;justify-content:center;
        font-size:14px;line-height:1;">🛒</div>`,
      className: "",
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });

    const marker = L.marker([poi.lat, poi.lng], { icon })
      .addTo(map)
      .bindPopup(
        `<div style="font-size:13px;font-weight:600;margin-bottom:2px;">${poi.name || "Supermarket"}</div>` +
        (distText ? `<div style="font-size:11px;color:#6b7280;">${distText}</div>` : "")
      );
    window._supermarketLayers.push(marker);
  });
}

function _showGymMarkers(listing) {
  const map = window._map;
  if (!map) return;
  const gyms = (listing.nearby_pois || {}).gyms || [];
  gyms.forEach(poi => {
    if (!poi.lat || !poi.lng) return;
    const distText = poi.distance_m
      ? poi.distance_m < 1000 ? `${poi.distance_m}m away` : `${(poi.distance_m / 1000).toFixed(1)}km away`
      : "";
    const icon = L.divIcon({
      html: `<div style="width:26px;height:26px;border-radius:50%;background:#dc2626;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;font-size:14px;line-height:1;">💪</div>`,
      className: "", iconSize: [26, 26], iconAnchor: [13, 13],
    });
    const marker = L.marker([poi.lat, poi.lng], { icon })
      .addTo(map)
      .bindPopup(
        `<div style="font-size:13px;font-weight:600;margin-bottom:2px;">${poi.name || "Gym"}</div>` +
        (distText ? `<div style="font-size:11px;color:#6b7280;">${distText}</div>` : "")
      );
    window._gymLayers.push(marker);
  });
}

function _showParkMarkers(listing) {
  const map = window._map;
  if (!map) return;
  const parks = (listing.nearby_pois || {}).parks || [];
  parks.forEach(poi => {
    if (!poi.lat || !poi.lng) return;
    const distText = poi.distance_m
      ? poi.distance_m < 1000 ? `${poi.distance_m}m away` : `${(poi.distance_m / 1000).toFixed(1)}km away`
      : "";
    const icon = L.divIcon({
      html: `<div style="width:26px;height:26px;border-radius:50%;background:#16a34a;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;font-size:14px;line-height:1;">🌳</div>`,
      className: "", iconSize: [26, 26], iconAnchor: [13, 13],
    });
    const marker = L.marker([poi.lat, poi.lng], { icon })
      .addTo(map)
      .bindPopup(
        `<div style="font-size:13px;font-weight:600;margin-bottom:2px;">${poi.name || "Park"}</div>` +
        (distText ? `<div style="font-size:11px;color:#6b7280;">${distText}</div>` : "")
      );
    window._parkLayers.push(marker);
  });
}

function toggleGymsOverlay() {
  window._showGyms = !window._showGyms;
  const btn = document.getElementById("gym-toggle");
  const knob = document.getElementById("gym-toggle-knob");
  if (btn) {
    btn.setAttribute("aria-checked", window._showGyms ? "true" : "false");
    btn.style.backgroundColor = window._showGyms ? "#dc2626" : "";
    btn.classList.toggle("bg-gray-200", !window._showGyms);
    btn.classList.toggle("dark:bg-gray-600", !window._showGyms);
  }
  if (knob) knob.style.transform = window._showGyms ? "translateX(16px)" : "";
  const map = window._map;
  if (map) { window._gymLayers.forEach(m => map.removeLayer(m)); window._gymLayers = []; }
  if (window._showGyms && window._expandedCardId !== null) {
    const listing = (window._listingById || {})[window._expandedCardId];
    if (listing) _showGymMarkers(listing);
  }
}

function toggleParksOverlay() {
  window._showParks = !window._showParks;
  const btn = document.getElementById("park-toggle");
  const knob = document.getElementById("park-toggle-knob");
  if (btn) {
    btn.setAttribute("aria-checked", window._showParks ? "true" : "false");
    btn.style.backgroundColor = window._showParks ? "#16a34a" : "";
    btn.classList.toggle("bg-gray-200", !window._showParks);
    btn.classList.toggle("dark:bg-gray-600", !window._showParks);
  }
  if (knob) knob.style.transform = window._showParks ? "translateX(16px)" : "";
  const map = window._map;
  if (map) { window._parkLayers.forEach(m => map.removeLayer(m)); window._parkLayers = []; }
  if (window._showParks && window._expandedCardId !== null) {
    const listing = (window._listingById || {})[window._expandedCardId];
    if (listing) _showParkMarkers(listing);
  }
}

function toggleSupermarketsOverlay() {
  window._showSupermarkets = !window._showSupermarkets;

  const btn = document.getElementById("supermarket-toggle");
  const knob = document.getElementById("supermarket-toggle-knob");
  if (btn) {
    btn.setAttribute("aria-checked", window._showSupermarkets ? "true" : "false");
    btn.style.backgroundColor = window._showSupermarkets ? "#0284c7" : "";
    btn.classList.toggle("bg-gray-200", !window._showSupermarkets);
    btn.classList.toggle("dark:bg-gray-600", !window._showSupermarkets);
  }
  if (knob) {
    knob.style.transform = window._showSupermarkets ? "translateX(16px)" : "";
  }

  // Clear existing supermarket markers
  const map = window._map;
  if (map) {
    window._supermarketLayers.forEach(m => map.removeLayer(m));
    window._supermarketLayers = [];
  }

  // If a card is expanded and toggle is now ON, show supermarkets immediately
  if (window._showSupermarkets && window._expandedCardId !== null) {
    const listing = (window._listingById || {})[window._expandedCardId];
    if (listing) _showSupermarketMarkers(listing);
  }
}

function clearMapOverlays() {
  const map = window._map;
  if (!map) return;
  window._supermarketLayers.forEach(m => map.removeLayer(m)); window._supermarketLayers = [];
  window._gymLayers.forEach(m => map.removeLayer(m)); window._gymLayers = [];
  window._parkLayers.forEach(m => map.removeLayer(m)); window._parkLayers = [];
  window._routeLayers.forEach(l => map.removeLayer(l)); window._routeLayers = [];
  const legend = document.getElementById("route-legend");
  if (legend) legend.classList.add("hidden");
}

function updateMarkerVisibility() {
  if (!window._map) return;

  const visibleIds = new Set();
  document.querySelectorAll(".listing-card-wrapper:not(.hidden)").forEach(wrapper => {
    visibleIds.add(parseInt(wrapper.dataset.listingId, 10));
  });

  if (window._clusterGroup) {
    // Rebuild cluster with only visible markers
    window._clusterGroup.clearLayers();
    visibleIds.forEach(id => {
      const marker = window._markerById[id];
      if (marker) window._clusterGroup.addLayer(marker);
    });
  } else {
    // Show/hide directly on map
    Object.entries(window._markerById).forEach(([id, marker]) => {
      if (visibleIds.has(parseInt(id, 10))) {
        if (!window._map.hasLayer(marker)) marker.addTo(window._map);
      } else {
        if (window._map.hasLayer(marker)) window._map.removeLayer(marker);
      }
    });
  }
}

function scoreColor(score) {
  if (score === null || score === undefined) return "#0ea5e9"; // blue — unscored
  if (score >= 70) return "#16a34a"; // green
  if (score >= 40) return "#ca8a04"; // yellow
  return "#dc2626";                  // red
}

function buildPopup(listing) {
  const price = listing.price_sek ? listing.price_sek.toLocaleString("sv-SE") + " kr/mo" : "–";
  const rooms = listing.rooms ? listing.rooms + " rum" : "–";
  const score = listing.ai_score != null
    ? `<span style="color:${scoreColor(listing.ai_score)};font-weight:600;">AI ${listing.ai_score}</span>`
    : `<span style="color:#0ea5e9;">Not scored</span>`;
  const commute = listing.commute_minutes
    ? `<div style="margin-top:4px;color:#2563eb;font-size:12px;">🚌 ${listing.commute_minutes} min to work</div>`
    : "";
  return `
    <div style="font-size:13px;min-width:160px;">
      <div style="font-weight:600;margin-bottom:4px;">${listing.title || "Listing"}</div>
      <div style="color:#6b7280;margin-bottom:4px;">${listing.district || ""}</div>
      <div>${price} &middot; ${rooms}</div>
      <div style="margin-top:4px;">${score}</div>
      ${commute}
    </div>`;
}

/* =====================================================================
   9. MOBILE MAP + SCORE / ENRICH ACTIONS (moved from index.html)
   ===================================================================== */
function toggleMobileMap() {
  const panel = document.getElementById("map-panel");
  const leftPanel = panel.previousElementSibling;
  const label = document.getElementById("map-toggle-label");
  const mapVisible = !panel.classList.contains("hidden");
  if (mapVisible) {
    panel.classList.add("hidden");
    leftPanel.style.display = "";
    if (label) label.textContent = "Map";
  } else {
    panel.classList.remove("hidden");
    panel.style.display = "flex";
    panel.style.height = "50vh";
    leftPanel.style.display = "none";
    if (label) label.textContent = "List";
    setTimeout(() => { if (window._map) window._map.invalidateSize(); }, 100);
  }
}

async function scoreListing(id, btn) {
  if (!btn) btn = document.getElementById(`score-btn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = 'Scoring…'; }
  try {
    const resp = await fetch(`/api/score/${id}`, { method: 'POST' });
    const data = await resp.json();
    if (data.success && data.score != null) {
      showToast(`Scored: ${data.score}/100 — reloading…`, 'success', 3000);
      setTimeout(() => window.location.reload(), 800);
    } else {
      const msg = data.error || 'Scoring failed';
      if (btn) { btn.textContent = 'Retry score'; btn.disabled = false; }
      showToast(msg.includes('API_KEY') ? 'Add ANTHROPIC_API_KEY to .env to enable AI scoring' : msg, 'error');
    }
  } catch (e) {
    if (btn) { btn.textContent = 'Score with AI'; btn.disabled = false; }
    showToast('Scoring request failed', 'error');
  }
}

async function scoreAll() {
  const btn = document.getElementById('score-all-btn');
  const txt = document.getElementById('score-all-btn-text');
  btn.disabled = true; txt.textContent = 'Scoring…';
  try {
    const resp = await fetch('/api/score-all', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      if (data.queued === 0) {
        showToast('All listings already scored.', 'info');
        btn.disabled = false; txt.textContent = 'Score All';
      } else {
        showToast(`Scoring ${data.queued} listing(s)… reloading in ~${Math.ceil(data.queued * 1.5)}s`, 'success', 10000);
        setTimeout(() => window.location.reload(), data.queued * 1500 + 3000);
      }
    } else {
      const msg = data.error || 'Unknown error';
      showToast(msg.includes('API_KEY') ? 'Add ANTHROPIC_API_KEY to .env to enable AI scoring' : msg, 'error');
      btn.disabled = false; txt.textContent = 'Score All';
    }
  } catch (e) {
    showToast('Score-all request failed', 'error');
    btn.disabled = false; txt.textContent = 'Score All';
  }
}

async function enrichAll() {
  const btn = document.getElementById('enrich-btn');
  const txt = document.getElementById('enrich-btn-text');
  btn.disabled = true; txt.textContent = 'Enriching…';
  try {
    const resp = await fetch('/api/enrich-all', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      if (data.queued === 0) {
        showToast('All listings already enriched.', 'info');
        btn.disabled = false; txt.textContent = 'Enrich';
      } else {
        const waitMs = Math.max(15000, data.queued * 10000);
        const msg = data.message.includes('overwrite mode')
          ? `Enriching ALL ${data.queued} listings (overwrite mode)… reloading in ~${Math.round(waitMs / 1000)}s`
          : `Enriching ${data.queued} listing(s)… reloading in ~${Math.round(waitMs / 1000)}s`;
        showToast(msg, 'success', waitMs);
        setTimeout(() => window.location.reload(), waitMs);
      }
    } else {
      showToast('Enrichment failed: ' + (data.error || 'Unknown error'), 'error');
      btn.disabled = false; txt.textContent = 'Enrich';
    }
  } catch (e) {
    showToast('Enrichment request failed', 'error');
    btn.disabled = false; txt.textContent = 'Enrich';
  }
}

/* =====================================================================
   10. INIT
   ===================================================================== */
// Keyboard navigation for lightbox
document.addEventListener("keydown", e => {
  const lb = document.getElementById("lightbox");
  if (!lb || lb.classList.contains("hidden")) return;
  if (e.key === "ArrowRight") lightboxNext();
  if (e.key === "ArrowLeft") lightboxPrev();
  if (e.key === "Escape") closeLightbox();
});

document.addEventListener("DOMContentLoaded", () => {
  // Build listing lookup index
  (window.LISTINGS_DATA || []).forEach(l => {
    window._listingById[l.id] = l;
  });

  // Read URL params and restore filter UI
  readUrlParams();
  restoreFilterUI();
  initDistrictFilters();

  // Init Leaflet map
  initMap();

  // Apply initial filters (handles sort + URL-restored filters)
  if (document.getElementById("listings-list")) {
    applyFilters();
  }
});
