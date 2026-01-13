const CACHE_NAME = 'poj-kesi-v1';
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

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
