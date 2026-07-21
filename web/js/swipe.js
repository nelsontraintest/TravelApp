import { formatDistance, haversineKm, DEMO_LOCATIONS } from "./geo.js";
import {
  clearPreferences,
  dislikePlace,
  getDislikes,
  getLikes,
  likePlace,
} from "./storage.js";

const deckEl = document.getElementById("deck");
const statusEl = document.getElementById("status");
const likeBtn = document.getElementById("like");
const nopeBtn = document.getElementById("nope");
const resetBtn = document.getElementById("reset");

let places = [];
let queue = [];
let current = null;

function setStatus(msg) {
  statusEl.textContent = msg;
}

async function loadPlaces() {
  // Relative path works on local serve and GitHub Pages (/TravelApp/web/...)
  const res = await fetch("../data/places.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Could not load places.json");
  const db = await res.json();
  places = (db.places || []).filter((p) => (p.origin || "kol") === "kol");
}

function rebuildQueue() {
  const liked = getLikes();
  const disliked = getDislikes();
  queue = places.filter((p) => !liked.has(p.id) && !disliked.has(p.id));
  // Prefer places with coordinates first
  queue.sort((a, b) => {
    const ac = a.location?.lat != null ? 0 : 1;
    const bc = b.location?.lat != null ? 0 : 1;
    return ac - bc;
  });
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function demoDistance(place) {
  const demo = DEMO_LOCATIONS["hk-central"];
  const loc = place.location || {};
  if (loc.lat == null || loc.lng == null) return "";
  const km = haversineKm(demo.lat, demo.lng, loc.lat, loc.lng);
  return `~${formatDistance(km)} from HK Central demo pin`;
}

function showEmpty() {
  current = null;
  deckEl.innerHTML = `
    <div class="panel empty" style="position:relative">
      <strong>Deck clear</strong>
      You've liked or skipped everything in the KOL list.
      Open Nearby to see suggestions tagged from your likes.
      <div style="margin-top:1rem">
        <button class="btn btn-ghost" type="button" id="reset-inline">Reset likes</button>
      </div>
    </div>`;
  document.getElementById("reset-inline")?.addEventListener("click", () => {
    clearPreferences();
    rebuildQueue();
    renderCard();
  });
  likeBtn.disabled = true;
  nopeBtn.disabled = true;
  setStatus(`Likes: ${getLikes().size} · Skips: ${getDislikes().size}`);
}

function renderCard() {
  likeBtn.disabled = false;
  nopeBtn.disabled = false;
  current = queue[0];
  if (!current) {
    showEmpty();
    return;
  }

  const tags = (current.tags || [])
    .slice(0, 5)
    .map((t) => `<span class="chip">${escapeHtml(t)}</span>`)
    .join("");

  deckEl.innerHTML = `
    <article class="swipe-card" id="card">
      <div class="stamp like" id="stamp-like">LIKE</div>
      <div class="stamp nope" id="stamp-nope">NOPE</div>
      <div class="meta">
        <span class="chip origin-kol">From KOL</span>
        <span class="chip">${escapeHtml(current.type)}</span>
        ${tags}
      </div>
      <h2>${escapeHtml(current.name)}</h2>
      <p class="muted">${escapeHtml(current.location?.city || "")}${
        current.location?.area ? " · " + escapeHtml(current.location.area) : ""
      }</p>
      <p class="desc">${escapeHtml(current.description || "")}</p>
      ${
        current.source?.quote
          ? `<p class="quote">${escapeHtml(current.source.quote)}</p>`
          : ""
      }
      <p class="muted">${escapeHtml(demoDistance(current))}</p>
    </article>
  `;

  wireDrag(document.getElementById("card"));
  setStatus(
    `${queue.length} left · Likes ${getLikes().size} · Skips ${getDislikes().size}`
  );
}

function decide(liked) {
  if (!current) return;
  if (liked) likePlace(current.id);
  else dislikePlace(current.id);
  queue.shift();
  renderCard();
}

function wireDrag(card) {
  if (!card) return;
  let startX = 0;
  let dx = 0;
  let dragging = false;
  const likeStamp = document.getElementById("stamp-like");
  const nopeStamp = document.getElementById("stamp-nope");

  const onStart = (x) => {
    dragging = true;
    startX = x;
    dx = 0;
  };
  const onMove = (x) => {
    if (!dragging) return;
    dx = x - startX;
    card.style.transform = `translateX(${dx}px) rotate(${dx / 28}deg)`;
    const abs = Math.min(1, Math.abs(dx) / 120);
    if (dx > 0) {
      likeStamp.style.opacity = String(abs);
      nopeStamp.style.opacity = "0";
    } else {
      nopeStamp.style.opacity = String(abs);
      likeStamp.style.opacity = "0";
    }
  };
  const onEnd = () => {
    if (!dragging) return;
    dragging = false;
    if (dx > 110) {
      decide(true);
      return;
    }
    if (dx < -110) {
      decide(false);
      return;
    }
    card.style.transform = "";
    likeStamp.style.opacity = "0";
    nopeStamp.style.opacity = "0";
  };

  card.addEventListener("pointerdown", (e) => {
    card.setPointerCapture(e.pointerId);
    onStart(e.clientX);
  });
  card.addEventListener("pointermove", (e) => onMove(e.clientX));
  card.addEventListener("pointerup", onEnd);
  card.addEventListener("pointercancel", onEnd);
}

likeBtn.addEventListener("click", () => decide(true));
nopeBtn.addEventListener("click", () => decide(false));
resetBtn.addEventListener("click", () => {
  clearPreferences();
  rebuildQueue();
  renderCard();
});

(async function init() {
  try {
    await loadPlaces();
    rebuildQueue();
    renderCard();
  } catch (err) {
    setStatus(err.message);
  }
})();
