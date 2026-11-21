/* Le Chronographe LÀ — service worker.
   Toujours le réseau d'abord : une page ou un corpus à jour s'affiche dès qu'il est en ligne.
   La copie locale ne sert qu'hors connexion (la page et la sphère restent lisibles).
   Le nom du cache change à chaque construction : ses anciennes copies sont effacées, jamais les caches d'un autre site
   servi depuis la même origine (ex. l'ancien Chronographe sur <compte>.github.io/chronographe). */
var PREFIXE = 'chronographe-la-nouvelle-edition-';   // n'efface jamais un cache d'un autre site de la même origine
var CACHE = PREFIXE + 'e02-b7d4a2329855-story-dbd54c7a';
var ESSENTIEL = ['/', '/commun/commun.css', '/commun/objet.css', '/commun/moteur.js', '/commun/carte.js', '/commun/actions.js',
  '/commun/objet.js', '/commun/recu.js', '/commun/polices/ebg-roman.woff2', '/commun/polices/ebg-italic.woff2',
  '/commun/media/b-fixe.jpg', '/corpus/edition-02.json', '/manifest.webmanifest',
  '/commun/story.js', '/commun/media/halo-story.jpg'];
self.addEventListener('install', function (e) { e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ESSENTIEL); }).then(function () { return self.skipWaiting(); })); });
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (k) { return Promise.all(k.filter(function (n) { return n.indexOf(PREFIXE) === 0 && n !== CACHE; }).map(function (n) { return caches.delete(n); })); }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== location.origin || r.headers.has('range')) return;
  e.respondWith(fetch(r).then(function (rep) {
    if (rep.ok && rep.type === 'basic') { var copie = rep.clone(); caches.open(CACHE).then(function (c) { c.put(r, copie); }); }
    return rep;
  }).catch(function () { return caches.open(CACHE).then(function (c) { return c.match(r).then(function (m) { return m || c.match('/'); }); }); }));
});
