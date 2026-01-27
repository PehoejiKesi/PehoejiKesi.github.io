const CACHE_NAME = 'poj-kesi-v2';
const urlsToCache = [
  './',
  './index.html',
  './style.css',
  './manifest.json',
  './img/favicon-16x16.png',
  './img/favicon-32x32.png',
  './img/apple-touch-icon.png',
  './img/pwa-192x192.png',
  './img/pwa-512x512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function (cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames.map(function (cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.mode === 'navigate') {
    // Network First for navigation requests (HTML)
    event.respondWith(
      fetch(event.request)
        .then(function (networkResponse) {
          return caches.open(CACHE_NAME).then(function (cache) {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(function () {
          return caches.match(event.request);
        })
    );
  } else {
    // Cache First for other assets
    event.respondWith(
      caches.match(event.request)
        .then(function (response) {
          if (response) {
            return response;
          }
          return fetch(event.request);
        })
    );
  }
});
