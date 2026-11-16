/* Le Chronographe LÀ — l'objet ouvert : l'heure de l'appareil et la rencontre du créneau en cours.
   Corpus lu dans /corpus/actuel.json (jamais généré) ; actions du lecteur dans actions.js. */
(function(){
'use strict';
var C=window.ChronoLA, A=window.ChronoActions, $=function(s){return document.querySelector(s);};
var reduit=matchMedia('(prefers-reduced-motion: reduce)').matches;

// la sphère animée (image fixe en mouvement réduit), en pause quand la page est cachée
if(!reduit){
  var s=$('[data-sphere]'), v=document.createElement('video');
  v.muted=true; v.setAttribute('muted',''); v.playsInline=true; v.setAttribute('playsinline',''); v.loop=true; v.autoplay=true;
  v.preload='metadata'; v.poster='/chronographe-la-essai/commun/media/b-fixe.jpg'; v.src='/chronographe-la-essai/commun/media/b-624.mp4'; v.setAttribute('aria-hidden','true');
  v.addEventListener('playing',function(){ var i=s.querySelector('img'); if(i) i.remove(); },{once:true});
  s.appendChild(v); var p=v.play(); if(p&&p.catch) p.catch(function(){});
  document.addEventListener('visibilitychange',function(){ if(document.hidden) v.pause(); else { var q=v.play(); if(q&&q.catch) q.catch(function(){}); } });
}

var premier=true;
function remplir(e){
  var h=$('[data-heure]'); h.textContent=e.heure; h.setAttribute('datetime',e.heure);
  var ph=$('[data-phrase]'), html=C.contenuHTML(e); if(ph.innerHTML===html) return;
  if(premier||reduit){ ph.innerHTML=html; premier=false; return; }
  ph.style.opacity=0; setTimeout(function(){ ph.innerHTML=html; ph.style.opacity=''; },450);   // le contenu change aux minutes 00, 10, 20…
}
document.addEventListener('click',function(ev){ if(!ev.target.closest('[data-sources]')) return;
  var d=$('#d-sources'); d.querySelector('[data-liste-sources]').innerHTML=C.sourcesHTML(C.etat().entree); d.showModal(); });

fetch('/chronographe-la-essai/corpus/actuel.json',{cache:'no-cache'}).then(function(r){return r.json();}).then(function(c){ C.charger(c); })
  .catch(function(){}).then(function(){ C.abonner(remplir); C.demarrer(); document.body.dataset.pret='1'; });

$('[data-partager]').onclick=function(){ A.partager(C.figer()); };   // figée au clic : heure, identifiant, version
$('[data-ajouter]').onclick=function(){ A.ajouter(); };
$('[data-propos]').onclick=function(){ $('#d-propos').showModal(); };
[].forEach.call(document.querySelectorAll('[data-fermer]'),function(b){ b.onclick=function(){ b.closest('dialog').close(); }; });
if('serviceWorker' in navigator && (location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')) navigator.serviceWorker.register('/chronographe-la-essai/sw.js').catch(function(){});
})();
