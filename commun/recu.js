/* Le Chronographe LÀ — écran de la minute partagée (et page d'accueil provisoire).
   La minute envoyée est écrite dans la page elle-même (#minute) : elle ne dépend jamais du corpus
   actuel et reste identique pour toujours, même après une correction du texte.
   « Ouvrir le Chronographe » lit le corpus actuel (/chronographe-la-essai/corpus/actuel.json) et suit l'heure de l'appareil. */
(function(){
'use strict';
var C=window.ChronoLA, $=function(s){return document.querySelector(s);};
var envoyee=JSON.parse($('#minute').textContent);          // null sur la page d'accueil
// iPhone seulement : ouverte depuis l'icône de l'écran d'accueil (certaines versions d'iOS enregistrent l'adresse
// de la page en cours plutôt que celle du Chronographe), la page mène à la minute du moment. Sur iPhone, un lien
// reçu ne s'ouvre jamais dans l'app de l'écran d'accueil ; sur Android, si, d'où la restriction à navigator.standalone.
if(envoyee && navigator.standalone===true && !document.referrer){ location.replace('/chronographe-la-essai/'); return; }
var reduit=matchMedia('(prefers-reduced-motion: reduce)').matches;
var mode='partagee', bloc=$('[data-bloc]'), etat=$('[data-etat]');

// la sphère animée remplace l'image fixe (sauf mouvement réduit)
if(!reduit){
  var s=$('[data-sphere]'), v=document.createElement('video');
  v.muted=true; v.setAttribute('muted',''); v.playsInline=true; v.setAttribute('playsinline',''); v.loop=true; v.autoplay=true;
  v.preload='metadata'; v.poster='/chronographe-la-essai/commun/media/b-fixe.jpg'; v.src='/chronographe-la-essai/commun/media/b-624.mp4'; v.setAttribute('aria-hidden','true');
  v.addEventListener('playing',function(){ var i=s.querySelector('img'); if(i) i.remove(); },{once:true});
  s.appendChild(v); var p=v.play(); if(p&&p.catch) p.catch(function(){});
  document.addEventListener('visibilitychange',function(){ if(document.hidden) v.pause(); else { var q=v.play(); if(q&&q.catch) q.catch(function(){}); } });
}

function remplir(e){ var h=$('[data-heure]'); h.textContent=e.heure; h.setAttribute('datetime',e.heure); $('[data-phrase]').innerHTML=C.noticeHTML(e); courante=e.entree; ajuster(); }

// Proportions : quand le texte est long, seule la sphère cède de la place (jusqu'à 62 % de sa taille prévue),
// pour que le bouton reste visible ; les caractères ne changent jamais. Sur un très petit écran, si cela ne
// suffit pas, la page défile légèrement plutôt que de comprimer la composition.
function ajuster(){
  var s=$('[data-sphere]'), b=$('.recu .agir:not([hidden]) button'); if(!s||!b) return;
  s.style.removeProperty('--t');
  var prevue=parseFloat(getComputedStyle(s).width), exces=b.getBoundingClientRect().bottom+window.scrollY-(innerHeight-12);
  if(exces>0) s.style.setProperty('--t', Math.max(prevue*0.62, prevue-exces*1.1)+'px');
}
addEventListener('resize',ajuster);
if(document.fonts&&document.fonts.ready) document.fonts.ready.then(ajuster);
var courante=envoyee;
ajuster();
// Sources de la notice affichée (liens consultables)
document.addEventListener('click',function(ev){ if(!ev.target.closest('[data-sources]')) return;
  $('[data-liste-sources]').innerHTML=C.sourcesHTML(courante); $('#d-sources').showModal(); });

var pret=fetch('/chronographe-la-essai/corpus/actuel.json',{cache:'no-cache'}).then(function(r){return r.json();}).then(function(c){ C.charger(c); })
  .catch(function(){ /* hors ligne : « texte à écrire » plutôt qu'une erreur */ });

function bascule(vers){
  var faire=function(){
    if(vers==='actuelle'){ C.modeDirect(); remplir(C.etat()); etat.textContent='Votre instant';
      $('[data-avant]').hidden=true; $('[data-apres]').hidden=false; $('[data-explication]').hidden=true; }
    else { remplir({heure:envoyee.heure, entree:envoyee}); etat.textContent='Un instant pour vous';
      $('[data-avant]').hidden=false; $('[data-apres]').hidden=true; $('[data-explication]').hidden=false; }
    mode=vers; bloc.classList.remove('sort'); etat.style.opacity=''; ajuster();
  };
  if(reduit){ faire(); return; }
  bloc.classList.add('sort'); etat.style.opacity=0; setTimeout(faire,450);
}
C.abonner(function(e){ if(mode==='actuelle' && e.mode==='direct') remplir(e); });   // la minute partagée, elle, ne bouge jamais
C.demarrer();
$('[data-decouvrir]').onclick=function(){ pret.then(function(){ bascule('actuelle'); }); };
$('[data-revoir]').onclick=function(){ bascule('partagee'); };
$('[data-propos]').onclick=function(){ $('#d-propos').showModal(); };
$('[data-ajouter]').onclick=function(){ window.ChronoActions.ajouter({surMinute:!!envoyee}); };   // aide propre à l'appareil
[].forEach.call(document.querySelectorAll('[data-fermer]'),function(b){ b.onclick=function(){ b.closest('dialog').close(); }; });

if('serviceWorker' in navigator && (location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')) navigator.serviceWorker.register('/chronographe-la-essai/sw.js').catch(function(){});
if(!envoyee){   // page d'accueil provisoire : directement la minute de l'appareil
  $('[data-revoir]').hidden=true; $('[data-avant]').hidden=true; $('[data-apres]').hidden=false; pret.then(function(){ mode='actuelle'; C.modeDirect(); remplir(C.etat()); });
}
})();
