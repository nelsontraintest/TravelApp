import { getLikes } from "./storage.js";

/** Score how similar a candidate is to the user's liked places (tag overlap). */
export function similarityScore(candidate, allPlaces, likedIds) {
  if (!likedIds.size) return 0;
  const liked = allPlaces.filter((p) => likedIds.has(p.id));
  if (!liked.length) return 0;

  const likedTags = new Set(liked.flatMap((p) => p.tags || []));
  const likedTypes = new Set(liked.map((p) => p.type));
  const likedCities = new Set(
    liked.map((p) => (p.location && p.location.city) || "").filter(Boolean)
  );

  let score = 0;
  for (const tag of candidate.tags || []) {
    if (likedTags.has(tag)) score += 2;
  }
  if (likedTypes.has(candidate.type)) score += 2;
  const city = (candidate.location && candidate.location.city) || "";
  if (city && likedCities.has(city)) score += 1;
  return score;
}

/**
 * Nearby results: KOL places + preference-origin places that match likes.
 * Preference suggestions are marked with reason "like_preference".
 * When cityFilter is set (All in area), includes places without lat/lng.
 */
export function rankNearby(places, { lat, lng, radiusKm, cityFilter, haversineKm }) {
  const likedIds = getLikes();
  const withDist = [];
  const cityKey = cityFilter ? cityFilter.toLowerCase() : "";

  for (const place of places) {
    const loc = place.location || {};
    const hasCoords = loc.lat != null && loc.lng != null;
    const placeCity = (loc.city || "").toLowerCase();

    if (cityKey) {
      if (placeCity !== cityKey) continue;
    } else if (!hasCoords) {
      continue;
    }

    let distanceKm;
    let ungeocoded = false;
    if (hasCoords) {
      distanceKm = haversineKm(lat, lng, loc.lat, loc.lng);
      if (!cityKey && distanceKm > radiusKm) continue;
    } else {
      distanceKm = Infinity;
      ungeocoded = true;
    }

    const origin = place.origin || "kol";
    const sim = similarityScore(place, places, likedIds);

    if (origin === "like_preference") {
      if (!likedIds.size || sim < 2) continue;
    }

    withDist.push({
      place,
      distanceKm,
      ungeocoded,
      suggestionReason:
        origin === "like_preference" ? "like_preference" : "kol",
      similarity: sim,
    });
  }

  withDist.sort((a, b) => {
    if (a.suggestionReason !== b.suggestionReason) {
      return a.suggestionReason === "kol" ? -1 : 1;
    }
    if (a.ungeocoded !== b.ungeocoded) {
      return a.ungeocoded ? 1 : -1;
    }
    return a.distanceKm - b.distanceKm;
  });

  return withDist;
}
