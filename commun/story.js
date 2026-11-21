/* Le Chronographe LÀ — « Partager en story » : carte verticale 1080 × 1920 (PNG), sans heure.
   Le fond « halo sphère » est une image fixe préparée à l'avance (la sphère agrandie et adoucie) : le téléphone n'a
   qu'à y écrire le texte de la rencontre, en EB Garamond, avec les polices du Chronographe.
   Le texte et les crédits viennent tels quels du corpus : jamais coupés, jamais reformulés. Seule la taille s'adapte
   à la longueur, dans des limites qui restent lisibles sur un téléphone.
   Usage : ChronoStory.ouvrir(notice)  ·  ChronoStory.dessiner(notice) → Promise<{canvas, mesures}>
   Fichier ajouté : il ne modifie ni le moteur, ni le corpus, ni le bouton « Partager cet instant ». */
(function (global) {
  'use strict';
  var L = 1080, H = 1920, ENCRE = '#121110', GRIS = '#58534d', SOURD = '#3f3b37';
  var FOND = '/commun/media/halo-story.jpg';
  // Instagram couvre environ 250 px en haut et 300 px en bas : le haut reste libre pour le message de la personne.
  var ZONE = { haut: 700, bas: 1500, signature: 1612, marge: 108 };

  function police(style, taille) { return (style || 'normal') + ' 400 ' + taille + 'px "EB Garamond", Garamond, serif'; }
  // affichage seulement : espace fine insécable avant » : ; ! ? et après « (les caractères du corpus ne changent pas)
  function typo(s) { return String(s).replace(/ ([»:;!?])/g, ' $1').replace(/« /g, '« '); }
  function lignes(ctx, texte, largeur) {
    var mots = typo(texte).split(' '), out = [], l = '';
    mots.forEach(function (m) { var e = l ? l + ' ' + m : m; if (ctx.measureText(e).width <= largeur || !l) l = e; else { out.push(l); l = m; } });
    if (l) out.push(l); return out;
  }
  // lignes équilibrées : même nombre de lignes, la plus petite largeur possible (pas de mot seul en fin de texte)
  function equilibre(ctx, texte, largeur) {
    var ls = lignes(ctx, texte, largeur), n = ls.length; if (n < 2) return ls;
    var bas = largeur * 0.5, haut = largeur;
    for (var k = 0; k < 14; k++) { var m = (bas + haut) / 2; if (lignes(ctx, texte, m).length > n) bas = m; else haut = m; }
    return lignes(ctx, texte, haut);
  }
  function bloc(ctx, texte, o) { ctx.font = police(o.style, o.taille); var ls = equilibre(ctx, texte, o.largeur);
    return { ls: ls, o: o, h: ls.length * o.taille * o.il }; }
  function espace(ctx, t, y, taille, track, couleur) {
    ctx.font = police('normal', taille); ctx.fillStyle = couleur;
    var w = 0, i; for (i = 0; i < t.length; i++) w += ctx.measureText(t[i]).width + (i < t.length - 1 ? track : 0);
    var x = (L - w) / 2; for (i = 0; i < t.length; i++) { ctx.fillText(t[i], x, y); x += ctx.measureText(t[i]).width + track; }
  }

  // Compose le contenu à la plus grande taille qui tient dans la zone, sans jamais couper le texte.
  function composer(ctx, n) {
    var larg = L - 2 * ZONE.marge, dispo = ZONE.bas - ZONE.haut, essais = [1, .94, .88, .82, .76, .7, .65, .6];
    for (var k = 0; k < essais.length; k++) {
      var f = essais[k], b = [];
      if (n.etiquette) b.push({ etiq: n.etiquette, h: 34, apres: 46 * f });
      if (n.type === 'mot') {
        var tm = 150 * f; ctx.font = police('normal', tm);
        while (ctx.measureText(n.mot).width > larg && tm > 60) { tm -= 4; ctx.font = police('normal', tm); }
        var mot = bloc(ctx, n.mot, { style: 'normal', taille: tm, il: 1.05, largeur: larg, couleur: ENCRE }); mot.apres = 30 * f; b.push(mot);
        if (n.grammaire) { var gr = bloc(ctx, n.grammaire, { style: 'italic', taille: Math.max(36, 42 * f), il: 1.3, largeur: larg, couleur: GRIS }); gr.apres = 44 * f; b.push(gr); }
        b.push(bloc(ctx, n.definition, { style: 'normal', taille: Math.max(40, 56 * f), il: 1.38, largeur: larg - 20, couleur: ENCRE }));
      } else {
        var t = n.lignes.join(' ');
        b.push(bloc(ctx, t, { style: 'normal', taille: Math.max(46, (t.length < 60 ? 86 : t.length < 110 ? 72 : 64) * f), il: 1.3, largeur: larg - 30, couleur: ENCRE }));
        // crédit exact du corpus, un peu plus grand et plus soutenu que dans la proposition
        if (n.extrait && n.signature) { var s = bloc(ctx, n.signature, { style: 'italic', taille: Math.max(38, 44 * f), il: 1.28, largeur: larg, couleur: SOURD }); b[b.length - 1].apres = 52 * f; b.push(s); }
      }
      var h = b.reduce(function (a, x) { return a + x.h + (x.apres || 0); }, 0);
      if (h <= dispo || k === essais.length - 1) return { blocs: b, hauteur: h, echelle: f };
    }
  }

  function charger(src) { return new Promise(function (ok, ko) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = ko; i.src = src; }); }
  function delai(p, ms) { return Promise.race([p, new Promise(function (ok) { setTimeout(ok, ms); })]); }

  function dessiner(n, opts) {
    opts = opts || {};
    var polices = ['400 60px "EB Garamond"', 'italic 400 40px "EB Garamond"'];
    var attente = document.fonts && document.fonts.load ? delai(Promise.all(polices.map(function (p) { return document.fonts.load(p); })), 4000) : Promise.resolve();
    return Promise.all([charger(opts.fond || FOND), attente]).then(function (r) {
      var c = document.createElement('canvas'); c.width = L; c.height = H; var ctx = c.getContext('2d');
      ctx.drawImage(r[0], 0, 0, L, H); ctx.textBaseline = 'alphabetic';
      var comp = composer(ctx, n), centre = (ZONE.haut + ZONE.bas) / 2, y = Math.max(ZONE.haut - 120, centre - comp.hauteur / 2), haut = y;
      comp.blocs.forEach(function (x) {
        if (x.etiq) { espace(ctx, x.etiq, y + 26, 28, 28 * 0.2, GRIS); y += x.h + x.apres; return; }
        ctx.font = police(x.o.style, x.o.taille); ctx.fillStyle = x.o.couleur;
        x.ls.forEach(function (l, i) { var base = y + i * x.o.taille * x.o.il + x.o.taille * 0.95; ctx.fillText(l, (L - ctx.measureText(l).width) / 2, base); });
        y += x.h + (x.apres || 0);
      });
      // signature : nom en capitales espacées, adresse un peu plus grande et plus soutenue
      espace(ctx, 'LE CHRONOGRAPHE LÀ', ZONE.signature, 34, 34 * 0.16, ENCRE);
      espace(ctx, 'chronographe.editionsla.com', ZONE.signature + 58, 38, 38 * 0.03, SOURD);
      return { canvas: c, mesures: { echelle: comp.echelle, haut: haut, bas: y, deborde: y > ZONE.signature - 60 } };
    });
  }
  function blob(c) { return new Promise(function (ok, ko) { try { c.toBlob(function (b) { b ? ok(b) : ko(new Error('toBlob')); }, 'image/png'); } catch (e) { ko(e); } }); }

  /* ---- fenêtre « Partager en story » ---- */
  var STYLE = '#d-story .apercu-story{margin:0 0 14px;text-align:center}' +
    '#d-story .apercu-story img{display:block;margin:0 auto;width:auto;max-width:100%;max-height:min(52vh,520px);border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.12);-webkit-touch-callout:default}' +
    '#d-story .boutons{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:6px 0 14px}' +
    '#d-story .boutons button{min-height:46px;padding:0 18px;border-radius:999px;border:1.5px solid #121110;font:inherit;font-size:17px;background:transparent;color:#121110}' +
    '#d-story .boutons .principal{background:#121110;color:#F6F3ED}#d-story .boutons button[hidden]{display:none}' +
    '#d-story .note,#d-story .etat{font-size:16px;line-height:1.4;color:#5f5a54;text-align:center;margin:8px 0 0}' +
    '#d-story .lien-manuel{display:block;width:100%;margin:8px 0 0;padding:10px 12px;font:inherit;font-size:16px;border:1px solid #cfc9c1;border-radius:8px;background:#fff;color:#121110}';
  function styler() { if (document.getElementById('style-story')) return; var s = document.createElement('style'); s.id = 'style-story'; s.textContent = STYLE; document.head.appendChild(s); }
  function lienRencontre(n) { return (location.protocol.indexOf('http') === 0 ? location.origin : 'https://chronographe.editionsla.com') + '/r/' + n.id + '/'; }
  function estIOS() { return /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); }

  function ouvrir(n, opts) {
    opts = opts || {}; styler();
    var d = document.getElementById('d-story');
    if (!d) { d = document.createElement('dialog'); d.id = 'd-story'; d.className = 'action story'; document.body.appendChild(d); }
    var url = lienRencontre(n), nom = 'chronographe-la-' + n.id + '.png', fichier = null, ios = estIOS();
    d.innerHTML = '<button class="fermer" type="button" data-fermer>Fermer</button><h2>Partager en story</h2>' +
      '<figure class="apercu-story"><img alt="Carte Story de la rencontre, à partager" data-story-img hidden><figcaption class="note" data-story-etat>Préparation de l’image…</figcaption></figure>' +
      '<p class="boutons"><button type="button" class="principal" data-story-partager hidden>Partager l’image</button>' +
      '<button type="button" data-story-enregistrer hidden>Enregistrer l’image</button>' +
      '<button type="button" data-story-lien>Copier le lien</button></p>' +
      '<p class="note">Dans Instagram, ajoutez l’image à votre story, puis l’autocollant « Lien » avec le lien copié.</p>' +
      '<p class="etat" role="status" aria-live="polite" data-story-statut></p>';
    var $ = function (s) { return d.querySelector(s); }, dire = function (t) { $('[data-story-statut]').textContent = t; };
    $('[data-fermer]').onclick = function () { d.close(); };

    // Copier le lien : presse-papiers si possible ; sinon, champ sélectionné à copier soi-même.
    $('[data-story-lien]').onclick = function () {
      var manuel = function () {
        var c = $('.lien-manuel'); if (!c) { c = document.createElement('input'); c.className = 'lien-manuel'; c.readOnly = true; c.value = url;
          c.setAttribute('aria-label', 'Lien de la rencontre'); $('[data-story-statut]').before(c); }
        c.focus(); c.select(); try { c.setSelectionRange(0, url.length); } catch (e) {}
        var ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
        dire(ok ? 'Lien copié.' : 'Copiez ce lien.');
      };
      if (navigator.clipboard && navigator.clipboard.writeText && global.isSecureContext !== false)
        navigator.clipboard.writeText(url).then(function () { dire('Lien copié.'); }, manuel);
      else manuel();
    };
    if (!d.open) d.showModal();

    return dessiner(n, opts).then(function (x) { return blob(x.canvas); }).then(function (b) {
      var img = $('[data-story-img]'); img.src = URL.createObjectURL(b); img.hidden = false;
      try { fichier = new File([b], nom, { type: 'image/png' }); } catch (e) { fichier = null; }
      var peutPartager = false;
      try { peutPartager = !!(fichier && navigator.canShare && navigator.share && navigator.canShare({ files: [fichier] })); } catch (e) {}
      var p = $('[data-story-partager]'), e = $('[data-story-enregistrer]');
      // 1. partage natif (iPhone, Android) : la feuille de partage du téléphone propose Instagram
      p.hidden = !peutPartager;
      p.onclick = function () {
        navigator.share({ files: [fichier] }).then(function () { dire('Image partagée.'); }).catch(function (err) {
          if (err && err.name === 'AbortError') return;
          e.hidden = false; dire(ios ? 'Le partage n’a pas abouti. Touchez longuement l’image, puis « Ajouter à Photos ».' : 'Le partage n’a pas abouti : enregistrez l’image.');
        });
      };
      // 2. secours : enregistrer le fichier (ordinateur, navigateurs sans partage de fichiers)
      e.hidden = peutPartager;
      e.onclick = function () { var a = document.createElement('a'); a.href = img.src; a.download = nom; document.body.appendChild(a); a.click(); a.remove();
        dire(ios ? 'Si l’image ne s’ajoute pas à Photos, touchez-la longuement, puis « Ajouter à Photos ».' : 'Image enregistrée.'); };
      $('[data-story-etat]').textContent = peutPartager ? 'Image prête, au format Story.' :
        (ios ? 'Image prête. Touchez-la longuement, puis « Ajouter à Photos ».' : 'Image prête, au format Story.');
      return { fichier: fichier, peutPartager: peutPartager };
    }).catch(function () {
      // 3. dernier secours : l'image n'a pas pu être préparée ; le lien reste disponible
      $('[data-story-etat]').textContent = 'L’image n’a pas pu être préparée sur cet appareil. Vous pouvez copier le lien, ou utiliser « Partager cet instant ».';
      return { fichier: null, peutPartager: false, erreur: true };
    });
  }
  global.ChronoStory = { dessiner: dessiner, blob: blob, ouvrir: ouvrir };
})(window);
