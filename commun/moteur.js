/* ==========================================================================
   Le Chronographe LÀ — moteur commun (nouvelle édition, projet autonome)
   © 2026 Éditions LÀ
   Un seul moteur pour tous les affichages : page dédiée, cartouche permanent,
   bloc d'accueil, module de fin de récit.
   - Heure : celle du terminal (new Date()), jamais de géolocalisation.
   - Recalcul : à chaque changement de minute, au retour d'onglet, à la reprise
     après veille, au retour depuis l'historique. Jamais d'addition de 60 s.
   - Modes : "direct" · "partagee" (minute conservée) · "demo" (heure d'exemple).
   - Contenu : lu dans un fichier de données séparé (corpus.json), jamais
     généré. Il change toutes les dix minutes (créneaux HH:00, HH:10 … HH:50) ;
     l'heure affichée reste l'heure réelle, à la minute.
     Deux sortes de contenus : un mot (mot, nature, genre, indication,
     définition courte, sources) ou un fragment littéraire (lignes,
     attribution, sources éventuelles).
     Le corpus des Éditions LÀ est la base permanente. Un contenu invité peut
     remplacer celui d'un créneau entre deux dates (incluses) ;
     à l'échéance, le contenu de base reprend sa place, sans intervention.
   ========================================================================== */
(function (global) {
  'use strict';
  if (global.ChronoLA) return;               // pas de doublon lors de la navigation

  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var horloge = function () { return new Date(); };   // remplaçable pour les tests
  var corpus = { edition: '', creneaux: {} };
  var abonnes = [];
  var minuterie = null, veille = null, derniereCle = null;
  var modeForce = null;                       // { mode, heure, id, version }

  function cle(d) { return pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  // Créneau de dix minutes d'une heure "HH:MM" : 03:17 → 03:10.
  function creneau(heure) { return heure.slice(0, 4) + '0'; }

  // Date locale "AAAA-MM-JJ" de l'appareil (les périodes d'invitation suivent le calendrier du lecteur).
  function jourLocal(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }

  // Un contenu : type "mot" (mot, nature, genre, indication, définition) ou "fragment" (lignes, attribution).
  var CHAMPS = ['id', 'version', 'type', 'mot', 'grammaire', 'nature', 'genre', 'indication', 'definition'];
  function copie(e, invite) {
    var c = {};
    for (var i = 0; i < CHAMPS.length; i++) if (e[CHAMPS[i]] != null) c[CHAMPS[i]] = e[CHAMPS[i]];
    if (e.lignes) c.lignes = e.lignes.slice();
    if (e.presentation && e.presentation.paragraphes) c.presentation = { paragraphes: e.presentation.paragraphes.slice() };
    if (e.attribution) c.attribution = { auteur: e.attribution.auteur, oeuvre: e.attribution.oeuvre };
    c.sources = (e.sources || []).map(function (s) { return { titre: s.titre, url: s.url }; });
    if (invite) { c.invite = true; c.auteur = e.auteur ? { nom: e.auteur.nom } : null; }
    return c;
  }

  /* ---- Rendu commun d'une notice (page, compositions, réception) -------- */
  // Affichage seulement (le corpus n'est pas modifié) : l'espace avant » : ; ! ? et après « devient insécable,
  // pour qu'un signe ne parte jamais seul en début de ligne.
  function typo(t) { return String(t).replace(/ ([»:;!?])/g, '\u00a0$1').replace(/« /g, '«\u00a0'); }
  function esc(t) { return typo(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  // Un mot à deux formes (« Circonspect, circonspecte ») passe à la ligne entre les formes, jamais dans un mot.
  function motHTML(m) {
    var f = String(m).split(/,\s*/);
    if (f.length < 2) return esc(m);   // un seul mot : la césure conditionnelle éventuelle reste possible
    return f.map(function (x, i) { return '<span class="forme">' + esc(x) + (i < f.length - 1 ? ',' : '') + '</span>'; }).join(' ');
  }
  // Indication grammaticale : la ligne du corpus telle quelle (« Nom féminin · Botanique ») ;
  // à défaut, l'ancienne forme en champs séparés (nature, genre, indication).
  function natureTexte(n) { return n.grammaire != null ? n.grammaire : n.nature + (n.genre ? ' ' + n.genre : '') + (n.indication ? ' · ' + n.indication : ''); }
  function credit(n) { return n.invite && n.auteur && n.auteur.nom ? '<p class="credit">Texte invité · ' + esc(n.auteur.nom) + '</p>' : ''; }
  function voir(n) { return n.sources && n.sources.length ? '<p class="voir"><button type="button" class="sources" data-sources>Sources</button></p>' : ''; }
  function attributionTexte(a) { return a ? [a.auteur, a.oeuvre].filter(Boolean) : []; }
  // Deux compositions dans la même identité : rien d'autre que la typographie ne distingue les catégories.
  function contenuHTML(e) {
    var n = e.entree;
    if (!n) return '<div class="contenu vide"><p class="a-ecrire">À venir · ' + creneau(e.heure) + '</p></div>';
    if (n.type === 'fragment') {
      var a = n.attribution;
      // Les blocs d'affichage viennent de l'indication de présentation quand elle existe ; sinon, le texte tel quel.
      var blocs = n.presentation && n.presentation.paragraphes ? n.presentation.paragraphes : n.lignes;
      return '<div class="contenu fragment">' + blocs.map(function (l) { return '<p class="texte">' + esc(l) + '</p>'; }).join('') +
        (a && (a.auteur || a.oeuvre) ? '<p class="attribution">' + (a.auteur ? esc(a.auteur) : '') + (a.auteur && a.oeuvre ? ', ' : '') + (a.oeuvre ? '<cite>' + esc(a.oeuvre) + '</cite>' : '') + '</p>' : '') +
        credit(n) + voir(n) + '</div>';
    }
    return '<div class="contenu mot-def"><p class="mot" lang="fr">' + motHTML(n.mot) + '</p>' +
      '<p class="nature">' + esc(natureTexte(n)) + '</p>' +
      '<p class="definition">' + esc(n.definition) + '</p>' + credit(n) + voir(n) + '</div>';
  }
  function sourcesHTML(n) {
    return '<ul class="liste-sources">' + (n && n.sources || []).map(function (s) {
      return '<li>' + (s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.titre) + '</a>' : esc(s.titre)) + '</li>';
    }).join('') + '</ul>';
  }

  // Texte affiché à une minute donnée : le texte invité actif à cette date, sinon le texte de base.
  // Sans date (minute partagée, démonstration) : le texte de base.
  function entree(heure, d) {
    heure = creneau(heure);
    if (d) {
      var inv = corpus.invites && corpus.invites[heure], j = jourLocal(d);
      for (var i = 0; inv && i < inv.length; i++) {
        if (inv[i].debut <= j && j <= inv[i].fin) return copie(inv[i], true);
      }
    }
    var e = corpus.creneaux && corpus.creneaux[heure];
    return e ? copie(e, false) : null;
  }

  // Retrouve un texte par son identifiant (base ou invité), pour une minute partagée.
  function parId(heure, id) {
    heure = creneau(heure);
    var e = corpus.creneaux && corpus.creneaux[heure];
    if (e && e.id === id) return copie(e, false);
    var inv = (corpus.invites && corpus.invites[heure]) || [];
    for (var i = 0; i < inv.length; i++) if (inv[i].id === id) return copie(inv[i], true);
    return null;
  }

  function etat() {
    if (modeForce) {
      var en = entree(modeForce.heure);
      // Minute partagée : on relit exactement le texte envoyé (id + version),
      // même si le corpus a été corrigé depuis (archives).
      if (modeForce.mode === 'partagee' && modeForce.id) {
        var arch = corpus.archives && corpus.archives[modeForce.id + '@' + modeForce.version];
        en = parId(modeForce.heure, modeForce.id);
        if (arch) en = copie(arch, !!arch.auteur);
        else if (!en) en = null;
        else if (String(en.version) !== String(modeForce.version)) en.revise = true;   // jamais en silence
      }
      var hm = modeForce.heure.split(':');
      return { mode: modeForce.mode, heure: modeForce.heure, entree: en, edition: corpus.edition,
               jour: (+hm[0] * 60 + +hm[1]) / 1440 };
    }
    var d = horloge();
    return { mode: 'direct', heure: cle(d), date: d, jour: (d.getHours() * 60 + d.getMinutes()) / 1440,
             entree: entree(cle(d), d), edition: corpus.edition };
  }

  function diffuser(force) {
    var e = etat();
    var marque = e.mode + '|' + e.heure;
    if (!force && marque === derniereCle) return;
    derniereCle = marque;
    for (var i = 0; i < abonnes.length; i++) {
      try { abonnes[i](e); } catch (err) { /* un affichage en échec n'arrête pas les autres */ }
    }
  }

  function planifier() {
    clearTimeout(minuterie);
    if (modeForce) return;
    var d = horloge();
    var reste = 60000 - (d.getSeconds() * 1000 + d.getMilliseconds()) + 40;
    minuterie = setTimeout(function () { diffuser(); planifier(); }, reste);
  }

  function resynchroniser() { diffuser(); planifier(); }

  function ecouter() {
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') resynchroniser();
    });
    global.addEventListener('pageshow', resynchroniser);   // retour arrière (bfcache)
    global.addEventListener('focus', resynchroniser);
    // Filet de sécurité : la veille peut geler les minuteries sans prévenir.
    // On compare seulement la clé ; rien n'est réaffiché si la minute n'a pas changé.
    veille = setInterval(function () { if (!modeForce) diffuser(); }, 15000);
  }

  /* ---- Lien de partage : la minute rencontrée, figée -------------------- */
  function lienPartage(e, base) {
    var u = new URL(base || global.location.href);
    u.search = ''; u.hash = '';
    u.searchParams.set('minute', e.heure.replace(':', ''));
    if (e.entree) {
      u.searchParams.set('texte', e.entree.id);
      u.searchParams.set('v', String(e.entree.version));
    }
    return u.toString();
  }

  function lirePartage(search) {
    var p = new URLSearchParams(search || global.location.search);
    var m = p.get('minute');
    if (!m || !/^([01]\d|2[0-3])[0-5]\d$/.test(m)) return null;
    return { mode: 'partagee', heure: m.slice(0, 2) + ':' + m.slice(2),
             id: p.get('texte'), version: p.get('v') };
  }

  global.ChronoLA = {
    charger: function (donnees) { corpus = donnees || corpus; diffuser(true); },
    abonner: function (fn) { abonnes.push(fn); fn(etat()); },
    etat: etat,
    figer: function () { return etat(); },            // instantané pour la carte de partage
    lienPartage: lienPartage,
    contenuHTML: contenuHTML,
    noticeHTML: contenuHTML,
    typo: typo,
    creneau: creneau,
    attributionTexte: attributionTexte,
    sourcesHTML: sourcesHTML,
    natureTexte: natureTexte,
    motHTML: motHTML,
    lirePartage: lirePartage,
    modeDirect: function () { modeForce = null; diffuser(true); planifier(); },
    modePartage: function (p) { modeForce = p; clearTimeout(minuterie); diffuser(true); },
    modeDemo: function (heure) { modeForce = { mode: 'demo', heure: heure || '03:17' };
                                 clearTimeout(minuterie); diffuser(true); },
    _horloge: function (fn) { horloge = fn || function () { return new Date(); }; resynchroniser(); },
    demarrer: function () { if (this._ok) return; this._ok = true; ecouter(); planifier(); }
  };
})(window);
