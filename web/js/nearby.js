import {
  formatDistance,
  getCurrentPosition,
  haversineKm,
  locationFromQuery,
} from "./geo.js";
import { rankNearby } from "./recommend.js";

const statusEl = document.getElementById("status");
const listEl = document.getElementById("list");
const radiusEl = document.getElementById("radius");
const demoEl = document.getElementById("demo");
const locateBtn = document.getElementById("locate");
const radiusAllEl = document.getElementById("radius-all");

let placesDb = { places: [], demo_pins: [] };
/** @type {Record<string, {lat:number,lng:number,label:string,city?:string,preview_url?:string}>} */
let demoLocations = {};
let userLoc = null;
let activePreviewId = null;

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
}

function isPreviewMode() {
  return userLoc?.source === "demo" && activePreviewId != null;
}

function syncRadiusOptions({ defaultAll = false } = {}) {
  if (!radiusAllEl) return;
  if (isPreviewMode()) {
    radiusAllEl.hidden = false;
    if (defaultAll || radiusEl.value === "all") {
      radiusEl.value = "all";
    }
  } else {
    radiusAllEl.hidden = true;
    if (radiusEl.value === "all") {
      radiusEl.value = "1";
    }
  }
}

function buildDemoPinOptions() {
  demoLocations = {};
  const pins = placesDb.demo_pins || [];
  demoEl.innerHTML = '<option value="">—</option>';
  for (const pin of pins) {
    if (!pin.id || pin.lat == null || pin.lng == null) continue;
    demoLocations[pin.id] = {
      lat: pin.lat,
      lng: pin.lng,
      label: pin.label || pin.id,
      city: pin.city,
      preview_url: pin.preview_url,
    };
    const opt = document.createElement("option");
    opt.value = pin.id;
    opt.textContent = pin.label || pin.id;
    demoEl.appendChild(opt);
  }
}

async function loadPlaces() {
  const res = await fetch("../data/places.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Could not load places.json");
  placesDb = await res.json();
  buildDemoPinOptions();
}

function getRankOptions() {
  const useAllInArea = isPreviewMode() && radiusEl.value === "all";
  const preview = activePreviewId ? demoLocations[activePreviewId] : null;
  return {
    lat: userLoc.lat,
    lng: userLoc.lng,
    radiusKm: useAllInArea ? Infinity : parseFloat(radiusEl.value) || 1,
    cityFilter: useAllInArea && preview?.city ? preview.city : null,
    haversineKm,
  };
}

function render() {
  listEl.innerHTML = "";
  if (!userLoc) {
    listEl.innerHTML =
      '<div class="empty"><strong>Waiting for location</strong>Tap the button to use your iPhone location, or pick a preview area.</div>';
    return;
  }

  const useAllInArea = isPreviewMode() && radiusEl.value === "all";
  const ranked = rankNearby(placesDb.places || [], getRankOptions());

  if (!ranked.length) {
    const hint = useAllInArea
      ? "No ingested places for this area yet."
      : "Try a larger radius, pick a preview area, or choose All in area.";
    listEl.innerHTML = `<div class="empty panel"><strong>No travel spots nearby</strong>Nothing from your KOL database (or like suggestions) in range. ${hint}</div>`;
    return;
  }

  ranked.forEach(({ place, distanceKm, suggestionReason }, i) => {
    const card = document.createElement("article");
    card.className = "place-card";
    card.style.animationDelay = `${i * 40}ms`;

    const originLabel =
      suggestionReason === "like_preference"
        ? "From your likes (not KOL)"
        : "From KOL video";

    const tags = (place.tags || [])
      .slice(0, 4)
      .map((t) => `<span class="chip">${escapeHtml(t)}</span>`)
      .join("");

    card.innerHTML = `
      <div class="row" style="justify-content:space-between">
        <h3>${escapeHtml(place.name)}</h3>
        <span class="distance">${formatDistance(distanceKm)}</span>
      </div>
      <div class="meta">
        <span class="chip">${escapeHtml(place.type)}</span>
        <span class="chip origin-${suggestionReason === "like_preference" ? "like" : "kol"}">${originLabel}</span>
        ${tags}
      </div>
      <p class="muted">${escapeHtml(place.description || place.location?.address || "")}</p>
      ${
        place.source?.quote
          ? `<p class="quote">${escapeHtml(place.source.quote)}</p>`
          : ""
      }
    `;
    listEl.appendChild(card);
  });
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function previewStatusMessage(demo) {
  const useAllInArea = radiusEl.value === "all";
  if (useAllInArea) {
    return `Previewing ${demo.label} (not your location) — all places in area`;
  }
  const radiusKm = parseFloat(radiusEl.value) || 1;
  const hint =
    radiusKm < 5 ? " — try All in area to see every ingested spot" : "";
  return `Previewing ${demo.label} (not your location)${hint}`;
}

async function locateFromDevice() {
  setStatus("Getting your location…");
  try {
    userLoc = await getCurrentPosition();
    activePreviewId = null;
    syncRadiusOptions();
    setStatus(
      `Located (±${Math.round(userLoc.accuracy || 0)} m). Showing spots within radius.`
    );
    demoEl.value = "";
    render();
  } catch (err) {
    setStatus(err.message, true);
  }
}

function applyDemo() {
  const key = demoEl.value;
  if (!key) {
    activePreviewId = null;
    syncRadiusOptions();
    userLoc = null;
    render();
    setStatus("Ready. Use your location on iPhone Safari (allow when prompted).");
    return;
  }
  const demo = demoLocations[key];
  if (!demo) return;
  activePreviewId = key;
  userLoc = { lat: demo.lat, lng: demo.lng, source: "demo" };
  syncRadiusOptions({ defaultAll: true });
  setStatus(previewStatusMessage(demo));
  render();
}

locateBtn.addEventListener("click", locateFromDevice);
radiusEl.addEventListener("change", () => {
  if (isPreviewMode()) {
    const demo = demoLocations[activePreviewId];
    if (demo) setStatus(previewStatusMessage(demo));
  }
  render();
});
demoEl.addEventListener("change", applyDemo);

(async function init() {
  try {
    await loadPlaces();
    const fromQuery = locationFromQuery();
    if (fromQuery) {
      userLoc = fromQuery;
      activePreviewId = null;
      syncRadiusOptions();
      setStatus("Location from link query (?lat=&lng=). Try 5–15 km radius if needed.");
      render();
    } else {
      syncRadiusOptions();
      render();
      setStatus("Ready. Use your location on iPhone Safari (allow when prompted).");
    }
  } catch (err) {
    setStatus(err.message, true);
  }
})();
