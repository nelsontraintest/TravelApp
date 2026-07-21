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
  const enrichment = place.enrichment || {};
  const loc = place.location || {};
  const url = enrichment.maps_url ||
    (loc.lat != null && loc.lng != null
      ? `https://www.google.com/maps/search/?api=1&query=${loc.lat},${loc.lng}`
      : "");
  if (!url) return "";
  return `<a class="action-link action-map" href="${escapeHtml(url)}" target="_blank" rel="noopener">地圖</a>`;
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
  const contact = contactHtml(place);
  if (!map && !contact) return "";
  return `<div class="action-row">${map}${contact}</div>`;
}

export function addressLine(place) {
  const loc = place.location || {};
  if (!loc.address) return "";
  return `<p class="address muted">${escapeHtml(loc.address)}</p>`;
}
