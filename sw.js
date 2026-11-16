/* Le Chronographe LÀ — service worker.
   Toujours le réseau d'abord : une page ou un corpus à jour s'affiche dès qu'il est en ligne.
   La copie locale ne sert qu'hors connexion (la page et la sphère restent lisibles).
   Le nom du cache change à chaque construction : ses anciennes copies sont effacées, jamais les caches d'un autre site
   servi depuis la même origine (ex. l'ancien Chronographe sur <compte>.github.io/chronographe). */
var PREFIXE = 'chronographe-la-nouvelle-edition-';   // n'efface jamais un cache d'un autre site de la même origine
var CACHE = PREFIXE + '492f55639786';
var ESSENTIEL = ['/chronographe-la-essai/', '/chronographe-la-essai/commun/commun.css', '/chronographe-la-essai/commun/objet.css', '/chronographe-la-essai/commun/moteur.js', '/chronographe-la-essai/commun/carte.js', '/chronographe-la-essai/commun/actions.js',
  '/chronographe-la-essai/commun/objet.js', '/chronographe-la-essai/commun/recu.js', '/chronographe-la-essai/commun/polices/ebg-roman.woff2', '/chronographe-la-essai/commun/polices/ebg-italic.woff2',
  '/chronographe-la-essai/commun/media/b-fixe.jpg', '/chronographe-la-essai/corpus/actuel.json', '/chronographe-la-essai/manifest.webmanifest'];
self.addEventListener('install', function (e) { e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ESSENTIEL); }).then(function () { return self.skipWaiting(); })); });
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (k) { return Promise.all(k.filter(function (n) { return n.indexOf(PREFIXE) === 0 && n !== CACHE; }).map(function (n) { return caches.delete(n); })); }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== location.origin || r.headers.has('range')) return;
  e.respondWith(fetch(r).then(function (rep) {
    if (rep.ok && rep.type === 'basic') { var copie = rep.clone(); caches.open(CACHE).then(function (c) { c.put(r, copie); }); }
    return rep;
  }).catch(function () { return caches.open(CACHE).then(function (c) { return c.match(r).then(function (m) { return m || c.match('/chronographe-la-essai/'); }); }); }));
});
