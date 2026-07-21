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

let placesDb = { places: [], demo_pins: [] };
/** @type {Record<string, {lat:number,lng:number,label:string,preview_url?:string}>} */
let demoLocations = {};
let userLoc = null;

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
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

function render() {
  listEl.innerHTML = "";
  if (!userLoc) {
    listEl.innerHTML =
      '<div class="empty"><strong>Waiting for location</strong>Tap the button to use your iPhone location, or pick a demo pin.</div>';
    return;
  }

  const radiusKm = parseFloat(radiusEl.value) || 1;
  const ranked = rankNearby(placesDb.places || [], {
    lat: userLoc.lat,
    lng: userLoc.lng,
    radiusKm,
    haversineKm,
  });

  if (!ranked.length) {
    listEl.innerHTML =
      '<div class="empty panel"><strong>No travel spots nearby</strong>Nothing from your KOL database (or like suggestions) within this radius. Try a larger radius (5–15 km for demo pins) or another area.</div>';
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

async function locateFromDevice() {
  setStatus("Getting your location…");
  try {
    userLoc = await getCurrentPosition();
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
  if (!key) return;
  const demo = demoLocations[key];
  if (!demo) return;
  userLoc = { lat: demo.lat, lng: demo.lng, source: "demo" };
  const radiusKm = parseFloat(radiusEl.value) || 1;
  const hint =
    radiusKm < 5
      ? " — try 5–15 km radius to see more spots in this area"
      : "";
  setStatus(`${demo.label} — demo pin (not GPS)${hint}`);
  render();
}

locateBtn.addEventListener("click", locateFromDevice);
radiusEl.addEventListener("change", render);
demoEl.addEventListener("change", applyDemo);

(async function init() {
  try {
    await loadPlaces();
    const fromQuery = locationFromQuery();
    if (fromQuery) {
      userLoc = fromQuery;
      setStatus("Location from link query (?lat=&lng=). Try 5–15 km radius if needed.");
      render();
    } else {
      render();
      setStatus("Ready. Use your location on iPhone Safari (allow when prompted).");
    }
  } catch (err) {
    setStatus(err.message, true);
  }
})();
