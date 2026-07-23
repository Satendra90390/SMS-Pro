const CACHE_NAME = 'edosaic-v2';
const STATIC_ASSETS = [
    '/',
    '/static/css/theme.css',
    '/static/css/style.css',
    '/static/css/auth.css',
    '/static/css/chat.css',
    '/static/css/landing.css',
    '/static/manifest.json',
    '/static/icons/icon-192.svg',
    '/static/icons/icon-512.svg',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch(() => {});
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;

    if (request.method !== 'GET') return;

    const url = new URL(request.url);

    // Dashboard/auth pages: network first, fallback to cache
    if (url.pathname.includes('/dashboard/') || url.pathname.includes('/login/') || url.pathname.includes('/verify/')) {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match(request);
            })
        );
        return;
    }

    // Landing page & static assets: stale-while-revalidate
    // Serve from cache instantly, update cache in background
    if (url.pathname === '/' || url.pathname.startsWith('/static/') || url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.match(request).then((cached) => {
                    const fetchPromise = fetch(request).then((response) => {
                        if (response && response.status === 200) {
                            cache.put(request, response.clone());
                        }
                        return response;
                    }).catch(() => {
                        // Server is down (Render cold start) — return cached version
                        return cached;
                    });

                    // Return cached version immediately if available, otherwise wait for network
                    return cached || fetchPromise;
                });
            })
        );
        return;
    }

    // Everything else: network first, fallback to cache
    event.respondWith(
        fetch(request).then((response) => {
            if (response && response.status === 200) {
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, clone);
                });
            }
            return response;
        }).catch(() => caches.match(request))
    );
});
