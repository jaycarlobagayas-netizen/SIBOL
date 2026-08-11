/* SIBOL service worker — offline-first cache.
   Bump CACHE when you deploy a new index.html or a rebuilt who-lms.json. */
const CACHE = "sibol-v2.2.0";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./who-lms.json"];

self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // who-lms.json may legitimately be absent; never fail the install over it
    await Promise.all(ASSETS.map(u => c.add(u).catch(() => null)));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    self.clients.claim();
  })());
});

/* Network-first so a redeploy is picked up, cache-first the moment the
   network is unavailable — which in a Mindanao classroom is the normal case. */
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith((async () => {
    try {
      const fresh = await fetch(req);
      const c = await caches.open(CACHE);
      c.put(req, fresh.clone());
      return fresh;
    } catch (_) {
      const hit = await caches.match(req);
      return hit || caches.match("./index.html");
    }
  })());
});
