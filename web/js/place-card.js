/**
 * Shared place card rendering helpers for Nearby and Swipe.
 */

export function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function localNameLine(place) {
  const names = place.names || {};
  const parts = [];
  if (names.ja && names.ja !== place.name) parts.push(names.ja);
  if (names["zh-Hant"] && names["zh-Hant"] !== place.name && names["zh-Hant"] !== names.ja) {
    parts.push(names["zh-Hant"]);
  }
  if (!parts.length) return "";
  return `<p class="local-name">${escapeHtml(parts.join(" / "))}</p>`;
}

export function photoHtml(place) {
  const photos = (place.enrichment || {}).photos || [];
  if (!photos.length) return "";
  return `<img class="place-photo" src="${escapeHtml(photos[0])}" alt="${escapeHtml(place.name)}" loading="lazy" />`;
}

export function mapsLink(place) {
  const loc = place.location || {};
  if (loc.lat == null || loc.lng == null) return "";
  const enrichment = place.enrichment || {};
  const url =
    enrichment.maps_url ||
    `https://www.google.com/maps/search/?api=1&query=${loc.lat},${loc.lng}`;
  if (!url) return "";
  return `<a class="action-link action-map" href="${escapeHtml(url)}" target="_blank" rel="noopener">地圖</a>`;
}

/** Google Search in Safari when there is no map pin. */
export function googleSearchQuery(place) {
  const loc = place.location || {};
  const names = place.names || {};
  const primary =
    place.name ||
    names.primary ||
    names.ja ||
    names.en ||
    names["zh-Hant"] ||
    "";
  const parts = [primary, loc.area, loc.city].filter(Boolean);
  return parts.join(" ").trim();
}

export function googleSearchLink(place) {
  const loc = place.location || {};
  // Only when there is no real pin
  if (loc.lat != null && loc.lng != null) return "";
  const q = googleSearchQuery(place);
  if (!q) return "";
  const url = `https://www.google.com/search?q=${encodeURIComponent(q)}`;
  return `<a class="action-link action-search" href="${escapeHtml(url)}" target="_blank" rel="noopener" title="${escapeHtml(q)}">搜尋</a>`;
}

export function isUngeocoded(place) {
  const loc = place.location || {};
  const status = (place.enrichment || {}).geocode_status;
  return loc.lat == null || loc.lng == null || status === "missing";
}

export function ungeocodedChip(place) {
  if (!isUngeocoded(place)) return "";
  return `<span class="chip chip-ungeocoded">位置未定</span>`;
}

/** Build a YouTube URL, optionally jumping to timestamp_sec. */
export function youtubeWatchUrl(place) {
  const source = place.source || {};
  const raw = (source.youtube_url || "").trim();
  if (!raw) return "";
  if (/SEED_DEMO/i.test(raw)) return "";
  const t = source.timestamp_sec;
  if (typeof t !== "number" || !Number.isFinite(t) || t < 0) return raw;
  const sec = Math.floor(t);
  try {
    const url = new URL(raw);
    url.searchParams.set("t", `${sec}`);
    return url.toString();
  } catch {
    const sep = raw.includes("?") ? "&" : "?";
    return `${raw}${sep}t=${sec}`;
  }
}

export function youtubeLink(place) {
  const url = youtubeWatchUrl(place);
  if (!url) return "";
  const title = (place.source || {}).youtube_title || "";
  const titleAttr = title ? ` title="${escapeHtml(title)}"` : "";
  return `<a class="action-link action-youtube" href="${escapeHtml(url)}" target="_blank" rel="noopener"${titleAttr}>影片</a>`;
}

export function contactHtml(place) {
  const contact = place.contact || {};
  const parts = [];
  if (contact.phone) {
    parts.push(`<a class="action-link action-phone" href="tel:${escapeHtml(contact.phone)}">${escapeHtml(contact.phone)}</a>`);
  }
  if (contact.website) {
    parts.push(`<a class="action-link action-web" href="${escapeHtml(contact.website)}" target="_blank" rel="noopener">網站</a>`);
  }
  return parts.join("");
}

export function quoteHtml(place) {
  const quote = (place.source || {}).quote;
  if (!quote) return "";
  return `<p class="quote">${escapeHtml(quote)}</p>`;
}

export function actionRow(place) {
  const map = mapsLink(place);
  const search = googleSearchLink(place);
  const youtube = youtubeLink(place);
  const contact = contactHtml(place);
  if (!map && !search && !youtube && !contact) return "";
  return `<div class="action-row">${map}${search}${youtube}${contact}</div>`;
}

export function addressLine(place) {
  const loc = place.location || {};
  if (!loc.address) return "";
  return `<p class="address muted">${escapeHtml(loc.address)}</p>`;
}
