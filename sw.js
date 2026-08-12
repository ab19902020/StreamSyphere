/*
 * Streams Sphere service worker.
 *
 * Deliberately conservative: the previous inline worker cached every request with a
 * cache-first strategy, so visitors kept being served a stale copy of the app long after
 * a deploy, and video/playlist responses were cached alongside it.
 *
 * Rules here:
 *   - the app shell is network-first with a cache fallback, so a deploy is picked up on
 *     the next load but the site still opens offline;
 *   - media, playlists and API calls are never cached — they are large, they expire, and
 *     a stale playlist is worse than no playlist;
 *   - old cache versions are dropped on activate.
 */

const CACHE = 'streams-sphere-v5';
const SHELL = ['/', '/Index.html', '/manifest.json'];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE)
            .then(cache => cache.addAll(SHELL).catch(() => {}))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

/** Streams, playlists and search results must always come from the network. */
function isUncacheable(url) {
    return /\.(m3u8?|ts|mp4|m4v|webm|ogv|mov|mkv)(\?|$)/i.test(url.pathname)
        || /archive\.org|iptv-org|githubusercontent|githack|advancedsearch|metadata/i.test(url.href)
        || /googletagmanager|google-analytics|doubleclick/i.test(url.href);
}

self.addEventListener('fetch', event => {
    const req = event.request;
    if (req.method !== 'GET') return;

    let url;
    try { url = new URL(req.url); } catch (e) { return; }
    if (!url.protocol.startsWith('http')) return;
    if (isUncacheable(url)) return;

    // Navigations and same-origin assets: network first, fall back to the cached shell.
    if (req.mode === 'navigate' || url.origin === self.location.origin) {
        event.respondWith(
            fetch(req)
                .then(res => {
                    if (res && res.ok && res.type === 'basic') {
                        const copy = res.clone();
                        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
                    }
                    return res;
                })
                .catch(() => caches.match(req).then(hit => hit || caches.match('/Index.html')))
        );
        return;
    }

    // Third-party assets (fonts, logos): cache first, they are immutable in practice.
    event.respondWith(
        caches.match(req).then(hit => hit || fetch(req).then(res => {
            if (res && (res.ok || res.type === 'opaque')) {
                const copy = res.clone();
                caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
            }
            return res;
        }).catch(() => hit))
    );
});
