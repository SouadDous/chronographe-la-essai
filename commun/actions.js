/* ==========================================================================
   Le Chronographe LÀ — actions du lecteur : partager une minute, enregistrer sa carte,
   ajouter le Chronographe à l'écran d'accueil.
   - Partager : la minute est figée au clic (heure exacte, identifiant, version). Tout ce qui suit
     (lien, carte, envoi) porte sur cette minute figée, même si le créneau change pendant l'envoi.
   - Envoyer le lien : feuille de partage du système quand elle existe, sinon copie du lien.
   - Enregistrer l'image : la carte est dessinée sur l'appareil (carte.js) ; partage du fichier
     sur téléphone (« Enregistrer l'image »), téléchargement sur ordinateur ; sur iPhone, l'aperçu
     peut aussi être enregistré par un appui long.
   - Ajouter à l'écran d'accueil : aide propre à l'appareil et au navigateur ; bouton d'installation
     direct quand le navigateur le propose (Chrome, Edge, Samsung Internet sur Android et ordinateur).
   ========================================================================== */
(function (global) {
  'use strict';
  var doc = document, C = global.ChronoLA;
  var CFG = global.CHRONO_ACTIONS || {};   // {base, promesse, invitation, adresse, essai, recu(slug) → url de démonstration}
  var differe = null;                      // invitation d'installation mise de côté (Chromium)
  global.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); differe = e; });
  global.addEventListener('appinstalled', function () { differe = null; });

  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  /* ---------- fenêtres ---------- */
  function fenetre(id, titre) {
    var d = doc.getElementById(id);
    if (!d) {
      d = doc.createElement('dialog'); d.id = id; d.className = 'action'; d.setAttribute('aria-labelledby', id + '-t');
      d.innerHTML = '<button class="fermer" type="button">Fermer</button><h2 id="' + id + '-t"></h2><div class="corps"></div>';
      d.querySelector('.fermer').onclick = function () { d.close(); };
      doc.body.appendChild(d);
    }
    d.querySelector('h2').textContent = titre;
    return d;
  }

  /* ---------- appareil ---------- */
  function plateforme(ua, nav) {
    ua = ua || navigator.userAgent; nav = nav || navigator;
    var installe = (global.matchMedia && matchMedia('(display-mode: standalone)').matches) || nav.standalone === true;
    var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && nav.maxTouchPoints > 1);
    var appli = /FBAN|FBAV|Instagram|Line\/|LinkedInApp|Snapchat|TikTok|Twitter|Pinterest|GSA\//.test(ua);
    if (installe) return 'installe';
    if (integre()) return 'integre';
    if (appli) return ios ? 'ios-appli' : 'android-appli';
    if (ios) return /CriOS|FxiOS|EdgiOS/.test(ua) ? 'ios-autre' : 'ios-safari';
    if (/Android/.test(ua)) return /SamsungBrowser/.test(ua) ? 'android-samsung' : /Firefox/.test(ua) ? 'android-firefox' : /Chrome/.test(ua) ? 'android-chrome' : 'android-autre';
    if (/Edg\/|Chrome\//.test(ua) && !/OPR\//.test(ua)) return 'bureau-chromium';
    if (/Macintosh/.test(ua) && /Safari\//.test(ua) && !/Chrome/.test(ua)) return 'mac-safari';
    if (/Firefox\//.test(ua)) return 'bureau-firefox';
    return 'autre';
  }
  // le Chronographe affiché dans une page d'un autre site (ex. une page Squarespace) : l'ajout porterait sur cette page
  function integre() { try { return global.self !== global.top; } catch (x) { return true; } }
  function etapes(p, surMinute) {
    var accueil = surMinute ? '<p class="note">Pour que l’icône ouvre toujours le Chronographe à l’heure du moment, faites l’ajout depuis le Chronographe : <a href="/chronographe-la-essai/">ouvrir le Chronographe</a>.</p>' : '';
    switch (p) {
      case 'integre': return '<p>Le Chronographe est présenté ici à l’intérieur d’une page du site. Ajoutée depuis cette page, l’icône ouvrirait la page du site, pas le Chronographe.</p><ol><li>Ouvrez le Chronographe à sa propre adresse : <a class="principal" href="/chronographe-la-essai/" target="_blank" rel="noopener" data-autonome>Ouvrir le Chronographe</a></li><li>Touchez à nouveau « Ajouter à mon écran d’accueil » et suivez l’aide.</li></ol>';
      case 'installe': return '<p>Le Chronographe LÀ est déjà sur votre écran d’accueil : vous l’avez ouvert depuis son icône.</p>';
      case 'ios-safari': return '<ol><li>Touchez le bouton <b>Partager</b> (le carré avec une flèche vers le haut).</li><li>Choisissez <b>Sur l’écran d’accueil</b>. Si l’option n’apparaît pas, faites défiler la liste.</li><li>Laissez <b>Ouvrir comme app web</b> activé s’il est proposé, puis touchez <b>Ajouter</b>.</li></ol>' + accueil;
      case 'ios-autre': return '<ol><li>Touchez le bouton <b>Partager</b> de votre navigateur.</li><li>Choisissez <b>Sur l’écran d’accueil</b>.</li><li>Touchez <b>Ajouter</b>.</li></ol><p class="note">Si l’option n’apparaît pas, ouvrez cette page dans Safari.</p>' + accueil;
      case 'ios-appli': case 'android-appli': return '<p>Vous lisez cette page dans une application (messagerie, réseau social). L’ajout à l’écran d’accueil n’y est pas possible.</p><ol><li>Ouvrez le menu de la page (<b>…</b> ou <b>⋮</b>).</li><li>Choisissez <b>Ouvrir dans ' + (p === 'ios-appli' ? 'Safari' : 'le navigateur') + '</b>.</li><li>Touchez ensuite à nouveau « Ajouter à mon écran d’accueil ».</li></ol>';
      case 'android-chrome': return '<ol><li>Touchez le menu <b>⋮</b> en haut à droite.</li><li>Choisissez <b>Ajouter à l’écran d’accueil</b>, puis <b>Installer</b> (ou <b>Installer l’application</b>).</li></ol>' + accueil;
      case 'android-samsung': return '<ol><li>Touchez le menu <b>≡</b> en bas.</li><li>Choisissez <b>Ajouter page à</b>, puis <b>Écran d’accueil</b>.</li></ol>' + accueil;
      case 'android-firefox': return '<ol><li>Touchez le menu <b>⋮</b>.</li><li>Choisissez <b>Ajouter à l’écran d’accueil</b> (ou <b>Installer</b>).</li></ol>' + accueil;
      case 'android-autre': return '<p>Ouvrez le menu de votre navigateur et cherchez <b>Ajouter à l’écran d’accueil</b>. Si l’option n’existe pas, ouvrez cette page dans Chrome.</p>';
      case 'bureau-chromium': return '<ol><li>Cliquez sur l’icône d’installation, à droite de la barre d’adresse,</li><li>ou ouvrez le menu <b>⋮</b> et choisissez <b>Installer Le Chronographe LÀ…</b> (selon la version : <b>Enregistrer et partager → Installer la page en tant qu’application</b>).</li></ol>';
      case 'mac-safari': return '<ol><li>Dans le menu <b>Fichier</b>, choisissez <b>Ajouter au Dock</b>.</li><li>Cliquez sur <b>Ajouter</b>.</li></ol>';
      case 'bureau-firefox': return '<p>Firefox ne permet pas d’installer un site sur ordinateur. Ajoutez la page à vos favoris, ou ouvrez-la dans Chrome, Edge ou Safari pour l’installer.</p>';
      default: return '<p>Ouvrez le menu de votre navigateur et cherchez <b>Ajouter à l’écran d’accueil</b> ou <b>Installer</b>.</p>';
    }
  }
  function ajouter(opts) {
    opts = opts || {};
    var p = plateforme(), d = fenetre('d-ajout', 'Ajouter à mon écran d’accueil'), c = d.querySelector('.corps');
    c.innerHTML = (differe && p !== 'installe' && p !== 'integre' ? '<p><button type="button" class="principal" data-installer>Ajouter Le Chronographe LÀ</button></p><p class="note">Ou, si vous préférez :</p>' : '') +
      etapes(p, opts.surMinute) + '<p class="note">L’icône ouvre le Chronographe à l’heure de votre appareil, avec le mot ou le fragment du moment.</p>';
    c.dataset.plateforme = p;
    var b = c.querySelector('[data-installer]');
    if (b) b.onclick = function () { differe.prompt(); differe.userChoice.then(function (r) { if (r && r.outcome === 'accepted') { differe = null; d.close(); } }); };
    d.showModal(); return p;
  }

  /* ---------- partage ---------- */
  // /m/1257-a1 (contenu de base a, version 1) ; /m/1257-i1-v1 (contenu invité i1, version 1)
  function slug(e) {
    if (!e.entree) return e.heure.replace(':', '');
    var s = e.entree.id.split('-')[1];
    return e.heure.replace(':', '') + '-' + (/^i\d+$/.test(s) ? s + '-v' : s) + e.entree.version;
  }
  function lien(e) {
    var base = CFG.base != null ? CFG.base : (location.protocol.indexOf('http') === 0 ? location.origin : '');
    return base + '/chronographe-la-essai/m/' + slug(e);
  }
  function resume(e) {
    var n = e.entree; if (!n) return e.heure;
    // texte intégral, jamais tronqué (un fragment fait au plus 170 signes)
    return e.heure + ' · ' + (n.type === 'mot' ? n.mot.replace(/­/g, '') : '«\u00a0' + n.lignes.join(' ').replace(/ ([»:;!?])/g, '\u00a0$1').replace(/« /g, '«\u00a0') + '\u00a0»');   // espaces insécables : affichage seulement
  }
  var courant = null;
  function partager(etat) {
    // la minute est figée ici, au clic : rien de ce qui suit ne relit l'horloge
    var f = JSON.parse(JSON.stringify({ heure: etat.heure, entree: etat.entree }));
    var url = lien(f), d = fenetre('d-partage', 'Partager cet instant'), c = d.querySelector('.corps');
    var peutEnvoyer = !!navigator.share;
    c.innerHTML = '<p class="fige" data-fige>' + esc(resume(f)) + '</p>' +
      '<p><label class="lien">Lien de cet instant<input type="text" readonly data-lien value="' + esc(url) + '"></label></p>' +
      '<p class="boutons">' + (peutEnvoyer ? '<button type="button" class="principal" data-envoyer>Envoyer le lien</button>' : '') +
      '<button type="button" class="' + (peutEnvoyer ? 'secondaire' : 'principal') + '" data-copier>Copier le lien</button>' +
      '<button type="button" class="secondaire" data-image disabled>Enregistrer l’image</button></p>' +
      '<p class="etat" role="status" data-statut></p>' +
      '<figure class="apercu"><img alt="Carte de l’instant partagé" data-apercu hidden><figcaption class="note" data-legende>Préparation de l’image…</figcaption></figure>' +
      (CFG.essai ? '<p class="note essai-note">' + CFG.essai + '</p>' : '') +
      (CFG.recu ? '<p class="note"><a href="' + esc(CFG.recu(slug(f))) + '" target="_blank" rel="noopener">Ouvrir la page reçue (démonstration)</a></p>' : '');
    var statut = c.querySelector('[data-statut]'); var dire = function (t) { statut.textContent = t; };
    var titre = 'Le Chronographe LÀ — ' + f.heure, texte = 'Un instant partagé : ' + resume(f);
    if (peutEnvoyer) c.querySelector('[data-envoyer]').onclick = function () {
      navigator.share({ title: titre, text: texte, url: url }).then(function () { dire('Lien envoyé.'); }).catch(function (x) { if (x && x.name !== 'AbortError') dire('L’envoi n’a pas abouti : copiez le lien.'); });
    };
    c.querySelector('[data-copier]').onclick = function () {
      var champ = c.querySelector('[data-lien]');
      var fin = function () { dire('Lien copié.'); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(fin, function () { champ.select(); doc.execCommand('copy'); fin(); });
      else { champ.select(); doc.execCommand('copy'); fin(); }
    };
    // la carte de la minute figée
    var nom = 'chronographe-la-' + f.heure.replace(':', 'h') + '.png', fichier = null;
    courant = global.ChronoCarte.dessiner({ heure: f.heure, contenu: f.entree, promesse: CFG.promesse, invitation: CFG.invitation, adresse: CFG.adresse }, { sphere: CFG.sphere })
      .then(function (x) { return global.ChronoCarte.blob(x.canvas).then(function (b) {
        fichier = new File([b], nom, { type: 'image/png' });
        var img = c.querySelector('[data-apercu]'); img.src = URL.createObjectURL(b); img.hidden = false;
        var ios = /^ios/.test(plateforme());
        c.querySelector('[data-legende]').textContent = ios ? 'Sur iPhone, vous pouvez aussi toucher longuement l’image, puis « Enregistrer dans Photos ».' : 'L’image de cet instant, au format 1080 × 1350.';
        var btn = c.querySelector('[data-image]'); btn.disabled = false;
        btn.onclick = function () {
          if (navigator.canShare && navigator.canShare({ files: [fichier] })) {
            navigator.share({ files: [fichier] }).then(function () { dire('Image prête.'); }).catch(function (x) { if (x && x.name !== 'AbortError') telecharger(); });
          } else telecharger();
        };
        function telecharger() { var a = doc.createElement('a'); a.href = img.src; a.download = nom; doc.body.appendChild(a); a.click(); a.remove(); dire('Image enregistrée dans vos téléchargements.'); }
        d.dataset.pret = '1'; return { mesures: x.mesures, fichier: fichier };
      }); }).catch(function () { c.querySelector('[data-legende]').textContent = 'L’image n’a pas pu être préparée sur cet appareil.'; d.dataset.pret = 'erreur'; });
    d.showModal();
    global.ChronoActions.dernier = { fige: f, url: url, carte: courant };   // pour les vérifications automatiques
    return global.ChronoActions.dernier;
  }

  // présenté dans la page d'un autre site : les liens vers le site s'ouvrent à la place de la page, jamais dans le cadre
  if (integre()) {
    var cibler = function () { [].forEach.call(doc.querySelectorAll('a[href^="http"]'), function (a) { if (a.host !== location.host && !a.target) a.target = '_top'; }); };
    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', cibler); else cibler();
  }

  global.ChronoActions = { partager: partager, ajouter: ajouter, plateforme: plateforme, lien: lien, slug: slug };
})(window);
