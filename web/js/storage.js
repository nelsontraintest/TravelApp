const LIKES_KEY = "scouted_likes_v1";
const DISLIKES_KEY = "scouted_dislikes_v1";

function readSet(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function writeSet(key, set) {
  localStorage.setItem(key, JSON.stringify([...set]));
}

export function getLikes() {
  return readSet(LIKES_KEY);
}

export function getDislikes() {
  return readSet(DISLIKES_KEY);
}

export function likePlace(id) {
  const likes = readSet(LIKES_KEY);
  const dislikes = readSet(DISLIKES_KEY);
  likes.add(id);
  dislikes.delete(id);
  writeSet(LIKES_KEY, likes);
  writeSet(DISLIKES_KEY, dislikes);
}

export function dislikePlace(id) {
  const likes = readSet(LIKES_KEY);
  const dislikes = readSet(DISLIKES_KEY);
  dislikes.add(id);
  likes.delete(id);
  writeSet(LIKES_KEY, likes);
  writeSet(DISLIKES_KEY, dislikes);
}

export function clearPreferences() {
  localStorage.removeItem(LIKES_KEY);
  localStorage.removeItem(DISLIKES_KEY);
}
