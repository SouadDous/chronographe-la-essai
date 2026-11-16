/* ==========================================================================
   Le Chronographe LÀ — l'image à enregistrer (1080 × 1350), dessinée dans le navigateur.
   Un seul code pour le téléphone du lecteur (« Enregistrer l'image ») et pour les exports de l'atelier.
   Règles, identiques à la page :
   - le texte est toujours intégral, à taille fixe ; seule la sphère cède de la place (620 → 360 px),
     puis les blancs autour du filet et en haut ; s'il reste de la place, l'ensemble est centré ;
   - un mot à deux formes passe à la ligne entre les formes, jamais dans un mot ;
   - un fragment suit son indication de présentation (blocs séparés par un blanc de 0,75 ligne) quand elle existe ;
   - les espaces avant » : ; ! ? et après « sont insécables (affichage seulement) ;
   - l'heure est dessinée après la sphère et sous son halo : chiffres noirs et nets.
   Usage : ChronoCarte.dessiner({heure, contenu, promesse, invitation, adresse}, {sphere: 'url'})
           → Promise<{canvas, mesures}> ;  ChronoCarte.blob(canvas) → Promise<Blob PNG>
   ========================================================================== */
(function (global) {
  'use strict';
  var L = 1080, H = 1350, MARGE_BAS = 80, LARGEUR = 900;
  var IVOIRE = '#F6F3ED', ENCRE = '#121110', GRIS = '#4B453F', SERIF = '"EB Garamond", Garamond, "Times New Roman", serif';

  function typo(t) { return String(t).replace(/ ([»:;!?])/g, ' $1').replace(/« /g, '« '); }
  function police(style, poids, taille) { return (style || 'normal') + ' ' + (poids || 400) + ' ' + taille + 'px ' + SERIF; }

  // Coupe en lignes (sans jamais couper un jeton), puis équilibre comme « text-wrap: balance ».
  function couper(ctx, jetons, max, sep) {
    sep = sep == null ? ' ' : sep;
    function glouton(w) {
      var lignes = [], cur = '';
      for (var i = 0; i < jetons.length; i++) {
        var essai = cur ? cur + sep + jetons[i] : jetons[i];
        if (!cur || ctx.measureText(essai).width <= w) cur = essai; else { lignes.push(cur); cur = jetons[i]; }
      }
      if (cur) lignes.push(cur);
      return lignes;
    }
    var base = glouton(max); if (base.length < 2) return base;
    var bas = max * 0.4, haut = max;
    for (var k = 0; k < 18; k++) { var mi = (bas + haut) / 2; if (glouton(mi).length > base.length) bas = mi; else haut = mi; }
    return glouton(haut);
  }
  function plusLarge(ctx, lignes) { return Math.max.apply(null, lignes.map(function (l) { return ctx.measureText(l).width; }).concat([0])); }

  // Un bloc de texte centré : {lignes, taille, hauteurLigne, police, couleur, avant}
  function bloc(ctx, texte, o) {
    ctx.font = o.police;
    var jetons = o.jetons || typo(texte).split(' ');
    var lignes = couper(ctx, jetons, o.largeur || LARGEUR, o.sep);
    return { lignes: lignes, taille: o.taille, lh: o.taille * o.hauteurLigne, police: o.police, couleur: o.couleur || ENCRE,
             avant: o.avant || 0, hauteur: lignes.length * o.taille * o.hauteurLigne, deborde: plusLarge(ctx, lignes) > (o.largeur || LARGEUR) + 1,
             espacement: o.espacement || 0, runs: o.runs || null };
  }
  function largeurEspacee(ctx, t, esp) { var w = 0; for (var i = 0; i < t.length; i++) w += ctx.measureText(t[i]).width; return w + esp * (t.length - 1); }

  function composer(ctx, d) {
    var c = d.contenu, blocs = [];
    var etiq = function (t, avant) { ctx.font = police('normal', 500, 27); return { lignes: [t.toUpperCase()], taille: 27, lh: 27 * 1.3, police: police('normal', 500, 27), couleur: ENCRE, avant: avant, hauteur: 27 * 1.3, espacement: 27 * 0.14 }; };
    var corps = [];
    if (!c) corps.push(bloc(ctx, 'À venir', { police: police('italic', 400, 30), taille: 30, hauteurLigne: 1.3, couleur: GRIS, avant: 30 }));
    else if (c.type === 'fragment') {
      var paras = (c.presentation && c.presentation.paragraphes) || c.lignes;
      paras.forEach(function (p, i) { corps.push(bloc(ctx, p, { police: police('normal', 400, 46.36), taille: 46.36, hauteurLigne: 1.28, avant: i ? 46.36 * 0.75 : 30 })); });
      var a = c.attribution;
      if (a && (a.auteur || a.oeuvre)) {
        // auteur en italique, titre de l'œuvre en romain, sur une seule ligne centrée
        var runs = []; if (a.auteur) runs.push([typo(a.auteur), 'italic']); if (a.auteur && a.oeuvre) runs.push([', ', 'italic']); if (a.oeuvre) runs.push([typo(a.oeuvre), 'normal']);
        corps.push({ lignes: [runs.map(function (r) { return r[0]; }).join('')], runs: runs, taille: 30.4, lh: 30.4 * 1.3, police: police('italic', 400, 30.4), couleur: GRIS, avant: 38 * 0.85, hauteur: 30.4 * 1.3 });
      }
    } else {
      var formes = String(c.mot).split(/,\s*/).map(function (f, i, t) { return f.replace(/­/g, '') + (i < t.length - 1 ? ',' : ''); });
      corps.push(bloc(ctx, '', { jetons: formes, police: police('normal', 400, 84), taille: 84, hauteurLigne: 1.04, avant: 30 }));
      var gram = c.grammaire != null ? c.grammaire : c.nature + (c.genre ? ' ' + c.genre : '') + (c.indication ? ' · ' + c.indication : '');
      corps.push(bloc(ctx, gram, { police: police('italic', 400, 31), taille: 31, hauteurLigne: 1.3, couleur: GRIS, avant: 31 * 0.45 }));
      corps.push(bloc(ctx, c.definition, { police: police('normal', 400, 38), taille: 38, hauteurLigne: 1.32, avant: 38 * 0.55 }));
    }
    if (c && c.invite && c.auteur && c.auteur.nom) corps.push(bloc(ctx, 'Texte invité · ' + c.auteur.nom, { police: police('italic', 400, 32), taille: 32, hauteurLigne: 1.3, couleur: GRIS, avant: 22 }));
    var fin = [
      etiq('Le Chronographe LÀ', 0),
      bloc(ctx, d.promesse, { police: police('normal', 400, 36), taille: 36, hauteurLigne: 1.32, avant: 16, largeur: 1000 }),
      bloc(ctx, d.invitation, { police: police('normal', 400, 36), taille: 36, hauteurLigne: 1.32, avant: 0, largeur: 1000 }),
      bloc(ctx, d.adresse, { police: police('normal', 400, 31), taille: 31, hauteurLigne: 1.3, avant: 22, largeur: 1000 })
    ];
    return { haut: etiq('Une minute partagée', 0), corps: corps, fin: fin };
  }

  function mise(comp, t, margeHaut, filetAvant, filetApres) {
    // positions verticales : étiquette, sphère (marges transparentes neutralisées), heure, contenu, filet, fin
    var y = margeHaut, pos = {};
    pos.etiquette = y; y += comp.haut.hauteur;
    pos.sphere = y - 10; y = pos.sphere + t - 30;
    pos.heure = y - 14; y = pos.heure + 146 * 0.9;
    pos.corps = []; comp.corps.forEach(function (b) { y += b.avant; pos.corps.push(y); y += b.hauteur; });
    y += filetAvant; pos.filet = y; y += 1.5 + filetApres;
    pos.fin = []; comp.fin.forEach(function (b) { y += b.avant; pos.fin.push(y); y += b.hauteur; });
    pos.bas = y; return pos;
  }

  function texte(ctx, b, top) {
    ctx.fillStyle = b.couleur; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    b.lignes.forEach(function (l, i) {
      ctx.font = b.police;
      var m = ctx.measureText('Hxg'), asc = m.fontBoundingBoxAscent || b.taille * 0.93, desc = m.fontBoundingBoxDescent || b.taille * 0.3;
      var base = top + i * b.lh + (b.lh - (asc + desc)) / 2 + asc;
      if (b.runs) {   // attribution : plusieurs styles sur une ligne
        var w = 0; b.runs.forEach(function (r) { ctx.font = police(r[1], 400, b.taille); w += ctx.measureText(r[0]).width; });
        var x = (L - w) / 2; b.runs.forEach(function (r) { ctx.font = police(r[1], 400, b.taille); ctx.fillText(r[0], x, base); x += ctx.measureText(r[0]).width; });
      } else if (b.espacement) {
        var x2 = (L - largeurEspacee(ctx, l, b.espacement)) / 2;
        for (var k = 0; k < l.length; k++) { ctx.fillText(l[k], x2, base); x2 += ctx.measureText(l[k]).width + b.espacement; }
      } else ctx.fillText(l, (L - ctx.measureText(l).width) / 2, base);
    });
  }

  function sphere(ctx, img, t, top) {
    var o = document.createElement('canvas'); o.width = o.height = Math.round(t);
    var g = o.getContext('2d'); g.drawImage(img, 0, 0, t, t);
    g.globalCompositeOperation = 'destination-in';
    var r = g.createRadialGradient(t * 0.5, t * 0.47, 0, t * 0.5, t * 0.47, t * 0.49);
    r.addColorStop(0, 'rgba(0,0,0,1)'); r.addColorStop(0.395 / 0.49, 'rgba(0,0,0,1)'); r.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = r; g.fillRect(0, 0, t, t);
    ctx.drawImage(o, (L - t) / 2, top);
  }

  function chargerImage(src) {
    return new Promise(function (ok, ko) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = ko; i.src = src; });
  }

  function dessiner(d, opts) {
    opts = opts || {};
    var polices = ['400 38px "EB Garamond"', 'italic 400 31px "EB Garamond"', '500 27px "EB Garamond"'];
    return Promise.all([chargerImage(opts.sphere || '/chronographe-la-essai/commun/media/b-fixe.jpg')].concat(document.fonts ? polices.map(function (p) { return document.fonts.load(p); }) : []))
      .then(function (r) {
        var img = r[0], canvas = document.createElement('canvas'); canvas.width = L; canvas.height = H;
        var ctx = canvas.getContext('2d'), comp = composer(ctx, d), cible = H - MARGE_BAS;
        var t = 620, haut = 92, fa = 44, fp = 36, pos = mise(comp, t, haut, fa, fp);
        if (pos.bas > cible) { t = Math.max(360, 620 - (pos.bas - cible)); pos = mise(comp, t, haut, fa, fp); }
        if (pos.bas > cible) { fa = 28; fp = 24; pos = mise(comp, t, haut, fa, fp); }
        if (pos.bas > cible) { haut = Math.max(56, 92 - (pos.bas - cible)); pos = mise(comp, t, haut, fa, fp); }
        if (pos.bas < cible - 4) { haut += (cible - pos.bas) / 2; pos = mise(comp, t, haut, fa, fp); }
        ctx.fillStyle = IVOIRE; ctx.fillRect(0, 0, L, H);
        texte(ctx, comp.haut, pos.etiquette);
        sphere(ctx, img, t, pos.sphere);
        texte(ctx, { lignes: [d.heure], taille: 146, lh: 146 * 0.9, police: police('normal', 400, 146), couleur: ENCRE }, pos.heure);   // devant la sphère
        comp.corps.forEach(function (b, i) { texte(ctx, b, pos.corps[i]); });
        ctx.globalAlpha = 0.55; ctx.fillStyle = ENCRE; ctx.fillRect((L - 56) / 2, pos.filet, 56, 1.5); ctx.globalAlpha = 1;
        comp.fin.forEach(function (b, i) { texte(ctx, b, pos.fin[i]); });
        var mesures = {
          heure: d.heure, bas: pos.bas, sphere: Math.round(t), hautHeure: pos.heure, basSphereOpaque: pos.sphere + 0.865 * t,
          deborde: pos.bas > H - 40 || comp.corps.concat(comp.fin).some(function (b) { return b.deborde; }),
          blocs: comp.corps.map(function (b) { return { lignes: b.lignes, taille: b.taille, avant: b.avant, interligne: b.lh }; })
        };
        return { canvas: canvas, mesures: mesures };
      });
  }
  function blob(canvas) { return new Promise(function (ok) { canvas.toBlob(ok, 'image/png'); }); }

  global.ChronoCarte = { dessiner: dessiner, blob: blob, typo: typo };
})(window);
