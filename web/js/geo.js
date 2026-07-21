/** Geolocation + distance helpers */

export function haversineKm(lat1, lng1, lat2, lng2) {
  const toRad = (d) => (d * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function formatDistance(km) {
  if (km == null || Number.isNaN(km)) return "";
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

/**
 * @returns {Promise<{lat:number,lng:number,accuracy?:number,source:string}>}
 */
export function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported in this browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          source: "device",
        });
      },
      (err) => {
        reject(new Error(err.message || "Location permission denied."));
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 }
    );
  });
}

/** Parse ?lat=&lng= from Shortcuts or shared links */
export function locationFromQuery(search = window.location.search) {
  const params = new URLSearchParams(search);
  const lat = parseFloat(params.get("lat"));
  const lng = parseFloat(params.get("lng"));
  if (Number.isFinite(lat) && Number.isFinite(lng)) {
    return { lat, lng, source: "query" };
  }
  return null;
}

export const DEMO_LOCATIONS = {
  "hk-central": { lat: 22.2815, lng: 114.1555, label: "Demo: HK Central" },
  "hk-tst": { lat: 22.294, lng: 114.172, label: "Demo: HK Tsim Sha Tsui" },
  tokyo: { lat: 35.6595, lng: 139.7005, label: "Demo: Tokyo Shibuya" },
};
