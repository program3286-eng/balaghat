// Service Worker - نظام إدارة البلاغات PWA
const CACHE_NAME = 'balaghat-v1';
const OFFLINE_URL = '/offline.html';

// الملفات المخزنة مؤقتاً للعمل بدون إنترنت
const PRECACHE_URLS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  OFFLINE_URL,
];

// ── تثبيت Service Worker ──
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_URLS).catch(() => {
        // تجاهل الأخطاء إذا لم يكن offline.html موجوداً بعد
      });
    }).then(() => self.skipWaiting())
  );
});

// ── تفعيل وتنظيف الكاش القديم ──
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── معالجة الطلبات ──
self.addEventListener('fetch', event => {
  // تجاهل طلبات non-GET
  if (event.request.method !== 'GET') return;

  // تجاهل طلبات الـ API والـ WebSocket
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/_stcore') || 
      url.pathname.startsWith('/stream') ||
      url.protocol === 'ws:' ||
      url.protocol === 'wss:') {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // حفظ نسخة في الكاش للملفات الثابتة
        if (url.pathname.startsWith('/static/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // عند انقطاع الإنترنت - ابحث في الكاش
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // إذا كان طلب صفحة، أظهر صفحة offline
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
        });
      })
  );
});

// ── استقبال رسائل من التطبيق ──
self.addEventListener('message', event => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});
