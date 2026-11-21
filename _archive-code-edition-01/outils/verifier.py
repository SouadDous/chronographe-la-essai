"""
Le Chronographe LÀ — vérifications automatiques du dossier de production, sur le corpus complet.

    python3 outils/verifier.py [--rapport controles/rapport.md]

Construit le site d'essai dans un dossier temporaire (rien n'est publié, le registre n'est pas touché), puis vérifie :
  1. le corpus : import fidèle (chaque texte identique au fichier éditorial), 144 créneaux, 72 mots, 72 fragments,
     phrase témoin à 03:10–03:19 ;
  2. le rythme : pour chacune des 1 440 minutes de la journée, le moteur affiche le contenu de son créneau,
     et le contenu ne change qu'aux minutes 00, 10, 20, 30, 40, 50 ;
  3. le partage : chacune des 1 440 adresses /m/… restitue exactement l'heure envoyée et le contenu du corpus ;
  4. l'affichage dans Chrome : les 144 contenus sur sept tailles d'écran (aucune coupure dans un mot, aucun
     débordement, aucun texte sous 18 px, bouton visible ou, sur les petits téléphones, accessible par un léger défilement) ;
  5. les images à enregistrer : les 144 cartes (texte intégral dans le cadre, caractères à taille fixe, heure dégagée de la sphère) ;
  6. les règles du corpus, de conservation et de statut, et les contenus invités.
"""
import argparse, asyncio, copy, functools, html.parser, http.server, json, pathlib, re, subprocess, sys, tempfile, threading, urllib.parse, contextlib, io, time
R = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / 'outils'))
import construire_site as CS, polices, importer_corpus as IC
from PIL import Image

ok = []; ko = []; journal = []
def test(nom, cond, detail=''):
    (ok if cond else ko).append(nom); ligne = ('  ✓ ' if cond else '  ✗ ') + nom + (f' — {detail}' if detail else '')
    print(ligne); journal.append(ligne)
def titre(t): print(t); journal.append('\n## ' + t)

class Metas(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.m = {}
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'meta' and ('property' in a or 'name' in a): self.m[a.get('property') or a.get('name')] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical': self.m['canonical'] = a.get('href')

CFG = json.loads((R / 'sources/config.json').read_text())
CORPUS = json.loads((R / 'sources/corpus/corpus.json').read_text())
ORIGINE = R / 'sources/corpus/origine/chronographe_la_144.json'
CRENEAUX = sorted(CORPUS['creneaux'])
TELEPHONES = [(320, 568), (360, 640), (375, 667), (390, 664), (390, 844), (430, 932)]
ORDINATEUR = [(1440, 900)]
PETITS = {(320, 568), (360, 640), (375, 667), (390, 664)}   # un léger défilement y est admis
LONG = '12:50'   # Synesthésie, la définition la plus longue

def nom_contenu(n): return n['mot'].replace('­', '') if n['type'] == 'mot' else '« ' + ' '.join(n['lignes'])[:34] + '… »'
def minute_de(c): return '03:17' if c == '03:10' else c[:4] + '7'
def slug_base(h): return h.replace(':', '') + '-a1'

def serveur(racine):
    class Silencieux(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    class Serveur(http.server.ThreadingHTTPServer):
        def handle_error(self, *a): pass   # lectures vidéo interrompues par la navigation : sans importance
    srv = Serveur(('127.0.0.1', 0), functools.partial(Silencieux, directory=str(racine)))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, f'http://127.0.0.1:{srv.server_address[1]}'

MESURE = """(()=>{const q=s=>document.querySelector(s), m=q('.mot'), tailles=[...document.querySelectorAll('.contenu p')].map(p=>parseFloat(getComputedStyle(p).fontSize));
  const segs = m ? (m.querySelector('.forme') ? [...m.querySelectorAll('.forme')] : [m]) : [];
  return {bas:q('[data-decouvrir]').getBoundingClientRect().bottom, min:Math.min(...tailles),
          coupe: segs.some(f => f.querySelector ? (f.classList.contains('forme') ? f.getClientRects().length>1 : f.getBoundingClientRect().height > parseFloat(getComputedStyle(f).fontSize)*1.5 && !/\\s/.test(f.textContent.trim())) : false),
          deborde:document.documentElement.scrollWidth>innerWidth || [...document.querySelectorAll('.contenu p')].some(p=>p.scrollWidth>p.clientWidth+1),
          orphelin:(()=>{ const w=document.createTreeWalker(document.querySelector('.contenu'),NodeFilter.SHOW_TEXT); let n, r=document.createRange();
            while((n=w.nextNode())){ const s=n.textContent; for(let i=1;i<s.length;i++){ if('»:;!?'.includes(s[i])){ r.setStart(n,i); r.setEnd(n,i+1); const a=r.getBoundingClientRect();
              r.setStart(n,i-1); r.setEnd(n,i); const b=r.getBoundingClientRect(); if(Math.abs(a.top-b.top)>2 && /\\s/.test(s[i-1])) return true; } } } return false; })()}})()"""

# ---------------------------------------------------------------- 1 · corpus
def corpus():
    titre('1 · Corpus')
    o = json.loads(ORIGINE.read_text())
    diff = IC.verifier_identite(o, CORPUS)
    test('import fidèle : chaque texte, mot, indication, source et statut identique au fichier éditorial', not diff, f'{len(o["entries"])} contenus comparés' if not diff else '; '.join(diff[:3]))
    attendus = [f'{h:02d}:{m:02d}' for h in range(24) for m in range(0, 60, 10)]
    test('couverture : 144 créneaux, de 00:00 à 23:50, sans trou ni doublon', CRENEAUX == attendus)
    types = [CORPUS['creneaux'][c]['type'] for c in CRENEAUX]
    test('72 mots et 72 fragments', types.count('mot') == 72 and types.count('fragment') == 72)
    ordre_source = [e['type'] for e in sorted(o['entries'], key=lambda e: e['start_minute_of_day'])]
    test('ordre composé conservé (aucun tirage, aucune alternance imposée)', types == ordre_source,
         f'{sum(1 for i in range(1, 144) if types[i] == types[i-1])} enchaînements de même type, comme dans le fichier fourni')
    test('phrase témoin dans le créneau 03:10–03:19', CORPUS['creneaux']['03:10']['lignes'] == ['Quelqu’un voudrait que cette minute passe. Quelqu’un voudrait qu’elle dure.'])
    test('aucune attribution d’auteur ni d’œuvre sur les fragments', not any('attribution' in CORPUS['creneaux'][c] for c in CRENEAUX))
    textes, e, _ = CS.verifier_corpus(CORPUS, {'textes': {}}, polices.caracteres())
    test('corpus accepté par la construction (limites, police, mots, sources)', not e, '; '.join(e[:3]))
    d = sorted((len(CORPUS['creneaux'][c]['definition']), CORPUS['creneaux'][c]['mot']) for c in CRENEAUX if CORPUS['creneaux'][c]['type'] == 'mot')
    f = sorted(len(CORPUS['creneaux'][c]['lignes'][0]) for c in CRENEAUX if CORPUS['creneaux'][c]['type'] == 'fragment')
    journal.append(f'  · définitions : {d[0][0]} à {d[-1][0]} signes (plus longues : ' + ', '.join(f'{m} {n}' for n, m in d[-3:][::-1]) + f') ; fragments : {f[0]} à {f[-1]} signes')

# ---------------------------------------------------------------- 2 · rythme (moteur, 1 440 minutes)
NODE = r"""
global.window=global; global.document={addEventListener(){}}; global.addEventListener=()=>{};
require(process.argv[1]); const C=window.ChronoLA; C.charger(JSON.parse(require('fs').readFileSync(process.argv[2],'utf8')));
const out={ids:[],html:{}}; const pad=n=>(n<10?'0':'')+n;
for(let m=0;m<1440;m++){ const h=pad(Math.floor(m/60))+':'+pad(m%60); C._horloge(()=>new Date(2026,10,16,Math.floor(m/60),m%60,30));
  const e=C.etat(); out.ids.push([h,e.heure,e.entree?e.entree.id:null]); if(m%10===7) out.html[h]=C.contenuHTML(e); }
C.modePartage({mode:'partagee',heure:'03:17',id:'c0310-a',version:'1'}); out.partage=C.etat();
console.log(JSON.stringify(out));
"""
def rythme():
    titre('2 · Rythme de dix minutes (moteur, 1 440 minutes)')
    r = json.loads(subprocess.run(['node', '-e', NODE, str(R / 'sources/scripts/moteur.js'), str(R / 'sources/corpus/corpus.json')], capture_output=True, text=True, check=True).stdout)
    ids = r['ids']
    test('heure affichée = heure réelle, pour chacune des 1 440 minutes', all(h == e for h, e, _ in ids))
    attendu = all(i == CORPUS['creneaux'][h[:4] + '0']['id'] for h, _, i in ids)
    test('chaque minute affiche le contenu de son créneau', attendu)
    changements = [ids[k][0] for k in range(1, 1440) if ids[k][2] != ids[k-1][2]]
    test('le contenu change exactement aux minutes 00, 10, 20, 30, 40, 50 (143 changements dans la journée, plus minuit)',
         len(changements) == 143 and all(h.endswith('0') for h in changements) and ids[0][2] != ids[-1][2])
    test('à 03:17, la phrase témoin', [i for h, _, i in ids if h == '03:17'] == ['c0310-a'])
    return r

# ---------------------------------------------------------------- 3 · partage (1 440 adresses)
def partage(site, r):
    titre('3 · Partage : restitution exacte (1 440 adresses)')
    pages = sorted((site / 'm').iterdir())
    test('1 440 adresses de minute, une par minute de la journée', len(pages) == 1440)
    erreurs = []
    for c in CRENEAUX:
        n = CORPUS['creneaux'][c]
        for m in CS.minutes_du_creneau(c):
            t = (site / 'm' / (m.replace(':', '') + '-a1') / 'index.html').read_text()
            d = json.loads(re.search(r'<script type="application/json" id="minute">(.*?)</script>', t, re.S).group(1).replace('<\\/', '</'))
            if d['heure'] != m or d['id'] != n['id'] or d['version'] != n['version'] or any(d.get(k) != n.get(k) for k in CS.CHAMPS):
                erreurs.append(m)
            if f'datetime="{m}">{m}</time>' not in t: erreurs.append(m + ' (heure écrite)')
    test('chaque adresse restitue l’heure envoyée et le contenu exact du corpus (texte, indication, sources)', not erreurs, ', '.join(erreurs[:5]))
    diff = [h for h, js in r['html'].items() if CS.notice_html({**CORPUS['creneaux'][h[:4] + '0'], 'heure': h[:4] + '0'}) != js]
    test('le texte écrit dans chaque page (lisible sans script) est identique à celui du moteur', not diff, ', '.join(diff[:5]))
    p = Metas(); p.feed((site / 'm/1257-a1/index.html').read_text())
    test('aperçu d’un mot : titre = heure + mot + définition intégrale', p.m.get('og:title') == '12:57 · Synesthésie — ' + CORPUS['creneaux'][LONG]['definition'])
    p2 = Metas(); p2.feed((site / 'm/0317-a1/index.html').read_text())
    test('aperçu d’un fragment : titre = heure + fragment, sans attribution', p2.m.get('og:title') == '03:17 · « Quelqu’un voudrait que cette minute passe. Quelqu’un voudrait qu’elle dure. »')
    test('aperçu : description avec la promesse', 'Toutes les dix minutes, une nouvelle rencontre' in p.m.get('og:description', ''))
    test('aperçu : adresse canonique et image versionnée', p.m.get('og:url') == 'https://chronographe.editionsla.com/m/1257-a1' and p.m.get('og:image') == 'https://chronographe.editionsla.com/apercus/s1/1257.jpg')
    tailles = [f.stat().st_size for f in (site / 'apercus/s1').iterdir()]
    test('1 440 images d’aperçu 1200 × 630, toutes sous 300 Ko', len(tailles) == 1440 and max(tailles) < 300 * 1024 and Image.open(site / 'apercus/s1/1257.jpg').size == (1200, 630),
         f'de {min(tailles)//1024} à {max(tailles)//1024} Ko')
    page = (site / 'm/0317-a1/index.html').read_text()
    test('les pages appellent la mise en page commune à adresse fixe : corriger l’affichage ne modifie aucune page publiée',
         '<script src="/commun/recu.js"></script>' in page and '<link rel="stylesheet" href="/commun/commun.css">' in page)
    test('aucun statut éditorial ni identifiant interne exposé dans les pages', 'proposed_for_review' not in page and 'previously_composed' not in page and 'statut' not in page)

# ---------------------------------------------------------------- 4 · affichage (Chrome)
async def affichage(site):
    from playwright.async_api import async_playwright
    titre('4 · Affichage des 144 contenus dans Chrome')
    srv, U = serveur(site); resultats = {}
    async with async_playwright() as p:
        b = await __import__('navigateur').lancer(p)
        for w, h in TELEPHONES + ORDINATEUR:
            # mouvement réduit : pas de transition pendant la mesure (la mise en page est la même)
            ctx = await b.new_context(viewport={'width': w, 'height': h}, reduced_motion='reduce'); pg = await ctx.new_page()
            erreurs_js = []; pg.on('pageerror', lambda e: erreurs_js.append(str(e)))
            mesures = {}
            for c in CRENEAUX:
                await pg.goto(f'{U}/m/{slug_base(minute_de(c))}/', wait_until='domcontentloaded')
                await pg.evaluate('document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))'); mesures[c] = await pg.evaluate(MESURE)
            await ctx.close(); resultats[(w, h)] = mesures
            coupes = [nom_contenu(CORPUS['creneaux'][c]) for c, r in mesures.items() if r['coupe']]
            deb = [nom_contenu(CORPUS['creneaux'][c]) for c, r in mesures.items() if r['deborde']]
            petits = [c for c, r in mesures.items() if r['min'] < 18]
            orphelins = [nom_contenu(CORPUS['creneaux'][c]) for c, r in mesures.items() if r['orphelin']]
            coupes += [f'signe isolé en début de ligne : {o}' for o in orphelins]
            caches = sorted(((r['bas'] - h, c) for c, r in mesures.items() if r['bas'] > h), reverse=True)
            base = not coupes and not deb and not petits and not erreurs_js
            if (w, h) in PETITS:
                test(f'{w}×{h} : 144 contenus sans coupure dans un mot ni signe isolé, sans débordement, aucun texte sous 18 px', base,
                     (f'bouton visible sans défiler pour {144 - len(caches)} contenus ; léger défilement pour {len(caches)} (au plus {round(caches[0][0])} px, '
                      f'{nom_contenu(CORPUS["creneaux"][caches[0][1]])})' if caches else 'bouton toujours visible sans défiler') + ('' if base else f' · coupés {coupes[:3]} · débordent {deb[:3]} · <18 px {petits[:3]}'))
            else:
                test(f'{w}×{h} : 144 contenus sans coupure ni signe isolé, sans débordement, aucun texte sous 18 px, bouton visible sans défiler', base and not caches,
                     ('' if not caches else f'{len(caches)} contenus demandent un défilement (au plus {round(caches[0][0])} px : {nom_contenu(CORPUS["creneaux"][caches[0][1]])})')
                     + ('' if base else f' · coupés {coupes[:3]} · débordent {deb[:3]} · <18 px {petits[:3]}'))
        # parcours à heure simulée sur le vrai corpus
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page()
        await pg.clock.install(time='2026-11-16T03:29:20'); await pg.goto(f'{U}/m/0317-a1/'); await pg.wait_for_load_state('networkidle')
        test('lien de 03:17 ouvert à 03:29 : la phrase témoin et l’heure envoyée', '03:17' in await pg.inner_text('[data-heure]') and 'Quelqu’un voudrait' in await pg.inner_text('[data-phrase]'))
        await pg.click('[data-decouvrir]'); await pg.clock.run_for(800)
        test('« Ouvrir le Chronographe » à 03:29 : heure réelle et contenu du créneau 03:20 (Étale)', '03:29' in await pg.inner_text('[data-heure]') and await pg.inner_text('.mot') == 'Étale')
        await pg.clock.run_for(60_000)
        test('à 03:30, nouveau contenu (fragment) ; l’heure suit la minute', '03:30' in await pg.inner_text('[data-heure]') and 'Le bébé dormait enfin' in await pg.inner_text('[data-phrase]'))
        await pg.clock.run_for(9 * 60_000)
        test('de 03:30 à 03:39, l’heure avance et le contenu reste le même', '03:39' in await pg.inner_text('[data-heure]') and 'Le bébé dormait enfin' in await pg.inner_text('[data-phrase]'))
        await pg.clock.run_for(60_000)
        test('à 03:40, nouveau contenu (Épure)', '03:40' in await pg.inner_text('[data-heure]') and await pg.inner_text('.mot') == 'Épure')
        await pg.click('[data-sources]'); await pg.wait_for_timeout(200)
        liens = await pg.eval_on_selector_all('#d-sources a', 'a=>a.map(x=>x.href)')
        test('« Sources » ouvre les références de vérification du mot affiché', liens == [CORPUS['creneaux']['03:40']['sources'][0]['url']], ', '.join(liens))
        await pg.click('#d-sources [data-fermer]'); await pg.click('[data-revoir]'); await pg.clock.run_for(800)
        test('« Revoir l’instant partagé » revient à 03:17 et à la phrase témoin', '03:17' in await pg.inner_text('[data-heure]') and 'Quelqu’un voudrait' in await pg.inner_text('[data-phrase]'))
        for m, attendu in [('03:41', 'Épure'), ('03:49', 'Épure')]:
            await pg.goto(f'{U}/m/{slug_base(m)}/'); a = (await pg.inner_text('[data-heure]'), await pg.inner_text('.mot'))
            test(f'adresse de {m} : sa minute et le contenu de son créneau', a == (m, attendu))
        await ctx.close()
        # mots à deux formes : passage à la ligne entre les formes, jamais dans un mot
        ctx = await b.new_context(viewport={'width': 320, 'height': 568}); pg = await ctx.new_page()
        await pg.goto(f'{U}/m/0817-a1/'); await pg.evaluate('document.fonts.ready')
        lignes = await pg.evaluate("[...document.querySelectorAll('.mot .forme')].map(f=>[f.textContent, f.getClientRects().length])")
        test('« Circonspect, circonspecte » à 320 px : retour à la ligne entre les deux formes, aucune forme coupée',
             len(lignes) == 2 and all(n == 1 for _, n in lignes) and await pg.evaluate("document.querySelector('.mot').getClientRects().length>0"), str(lignes))
        await ctx.close()
        await b.close()
    srv.shutdown()
    return resultats

# ---------------------------------------------------------------- 5 · cartes (carte.js, le code du téléphone)
async def cartes(site):
    from playwright.async_api import async_playwright
    titre('5 · Images à enregistrer (1080 × 1350), dessinées par carte.js')
    (site / '_rendu.html').write_bytes((R / 'sources/gabarits/rendu.html').read_bytes())
    srv, U = serveur(site); res = {}
    cas = [(c, CORPUS['creneaux'][c]) for c in CRENEAUX] + [
        ('09:00x', {'type': 'mot', 'mot': 'Incommen­surabilité, incommensurables', 'grammaire': 'Nom féminin · Cas limite', 'definition': ('Caractère de ce qui ne peut être mesuré, faute de commune mesure ; par extension, ce qui dépasse toute évaluation possible, toute comparaison raisonnable, toute échelle humaine connue.')[:180]}),
        ('09:10x', {'type': 'fragment', 'lignes': [('Il y a des heures que l’on traverse sans les voir, et d’autres qui demeurent, posées sur la table comme une lettre que l’on n’ose pas encore ouvrir, ni tout à fait ranger.')[:170]], 'attribution': {'auteur': 'Attribution d’essai'}})]
    async with async_playwright() as p:
        b = await __import__('navigateur').lancer(p); pg = await b.new_page(viewport={'width': 1080, 'height': 1350})
        for c, n in cas:
            h = minute_de(c[:5])
            d = {'heure': h, 'contenu': n, 'promesse': CFG['promesse'], 'invitation': CFG['invitation'], 'adresse': CFG['adresse_ecrite']}
            await pg.goto('about:blank'); await pg.goto(f'{U}/_rendu.html#carte/' + urllib.parse.quote(json.dumps(d, ensure_ascii=False)))
            await pg.wait_for_function('document.body.dataset.pret==="1"')
            res[c] = await pg.evaluate('window.mesuresCarte')
        await b.close()
    srv.shutdown(); (site / '_rendu.html').unlink()
    def bon(c, m, n):
        tailles = [x['taille'] for x in m['blocs']]
        attendu = (84 in tailles and 38 in tailles) if n['type'] == 'mot' else (46.36 in tailles)
        return not m['deborde'] and m['bas'] <= 1271 and attendu and m['hautHeure'] >= m['basSphereOpaque'] - 1
    reel = {c: m for c, m in res.items() if not c.endswith('x')}
    mauvais = [nom_contenu(CORPUS['creneaux'][c]) for c, m in reel.items() if not bon(c, m, CORPUS['creneaux'][c])]
    sph = sorted(m['sphere'] for m in reel.values())
    test('144 cartes : texte intégral dans le cadre, marge de 80 px, caractères à taille fixe, heure sous le halo', not mauvais,
         f'sphère de {sph[0]} à {sph[-1]} px selon la longueur du texte' + (f' · à revoir : {mauvais[:5]}' if mauvais else ''))
    for c in ['12:50', '16:50', '03:40', '08:10']:
        m = reel[c]; test(f'carte · {nom_contenu(CORPUS["creneaux"][c])} ({len(CORPUS["creneaux"][c]["definition"])} signes)', bon(c, m, CORPUS['creneaux'][c]), f'adresse finit à {round(m["bas"])} px, sphère {m["sphere"]} px')
    m = reel['03:10']
    test('carte de 03:17 : la phrase témoin en deux blocs, selon l’indication de présentation',
         [x['lignes'] for x in m['blocs']][:2] == [['Quelqu’un voudrait que cette minute passe.'], ['Quelqu’un voudrait qu’elle dure.']] or
         [' '.join(x['lignes']) for x in m['blocs']][:2] == ['Quelqu’un voudrait que cette minute passe.', 'Quelqu’un voudrait qu’elle dure.'])
    m = reel['12:50']
    test('carte : espaces insécables autour des guillemets, comme sur la page', any('« voix rugueuse »' in l for x in m['blocs'] for l in x['lignes']))
    m = reel['08:10']
    test('carte : « Circonspect, circonspecte » sans coupure dans un mot', all(l in ('Circonspect,', 'circonspecte', 'Circonspect, circonspecte') for l in m['blocs'][0]['lignes']), str(m['blocs'][0]['lignes']))
    for c in ['09:00x', '09:10x']:
        m = res[c]; test(f'carte · cas limite {"mot à deux formes, définition de 180 signes" if c == "09:00x" else "fragment de 170 signes avec attribution"}',
                         not m['deborde'] and m['bas'] <= 1271, f'adresse finit à {round(m["bas"])} px, sphère {m["sphere"]} px')
    return res

# ---------------------------------------------------------------- 8 · parcours complet du lecteur
UA = {
    'iphone-safari': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1',
    'iphone-chrome': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/131.0.6778.73 Mobile/15E148 Safari/604.1',
    'iphone-instagram': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 355.0.0.0',
    'android-chrome': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
    'android-samsung': 'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Mobile Safari/537.36',
    'mac-safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
    'bureau-firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
}
PARTAGE_FACTICE = """window.__partages=[]; navigator.share=function(d){ window.__partages.push({url:d.url||null, title:d.title||null, fichiers:(d.files||[]).map(f=>({nom:f.name,type:f.type,taille:f.size}))}); return Promise.resolve(); };
navigator.canShare=function(d){ return true; };"""

async def parcours(site):
    from playwright.async_api import async_playwright
    titre('8 · Parcours complet : le Chronographe, le partage, la page reçue, l’écran d’accueil')
    srv, U = serveur(site)
    async with async_playwright() as p:
        b = await __import__('navigateur').lancer(p)
        # A · ouvrir le Chronographe à 12:57, partager Synesthésie, ouvrir le lien reçu à une autre heure
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, user_agent=UA['iphone-safari'], reduced_motion='reduce'); pg = await ctx.new_page()
        await ctx.add_init_script(PARTAGE_FACTICE); await pg.clock.install(time='2026-11-16T12:57:20')
        await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"'); await pg.clock.run_for(300)
        test('le Chronographe ouvert à 12:57 : Synesthésie, heure de l’appareil', await pg.inner_text('[data-heure]') == '12:57' and await pg.inner_text('.mot') == 'Synesthésie')
        await pg.click('[data-partager]'); await pg.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
        url = await pg.input_value('[data-lien]')
        test('« Partager cet instant » : lien de la minute exacte et de sa version', url == U + '/m/1257-a1', url)
        await pg.click('[data-envoyer]'); envoi = await pg.evaluate('window.__partages')
        test('« Envoyer le lien » ouvre la feuille de partage du téléphone avec ce lien', envoi and envoi[0]['url'] == url, str(envoi[:1]))
        await pg.click('[data-image]'); await pg.wait_for_timeout(300); envoi = await pg.evaluate('window.__partages')
        test('« Enregistrer l’image » transmet la carte de cette minute (PNG) au téléphone', len(envoi) == 2 and envoi[1]['fichiers'] and envoi[1]['fichiers'][0]['type'] == 'image/png' and envoi[1]['fichiers'][0]['nom'] == 'chronographe-la-12h57.png' and envoi[1]['fichiers'][0]['taille'] > 100_000,
             str(envoi[1]['fichiers'] if len(envoi) > 1 else ''))
        carte = await pg.evaluate('ChronoActions.dernier.carte.then(x=>x.mesures)')
        test('la carte porte 12:57 et la définition intégrale de Synesthésie', carte['heure'] == '12:57' and ' '.join(carte['blocs'][2]['lignes']).replace(' ', ' ') == CORPUS['creneaux']['12:50']['definition'])
        await ctx.close()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce'); pg = await ctx.new_page()
        await pg.clock.install(time='2026-11-17T08:03:10'); await pg.goto(url); await pg.wait_for_load_state('networkidle')
        definition = (await pg.inner_text('.definition')).replace(' ', ' ')
        test('lien ouvert le lendemain à 08:03 : le destinataire retrouve 12:57 et le texte exact', await pg.inner_text('[data-heure]') == '12:57' and definition == CORPUS['creneaux']['12:50']['definition'])
        await pg.click('[data-decouvrir]'); await pg.clock.run_for(800)
        test('puis « Ouvrir le Chronographe » : 08:03 et la rencontre du créneau 08:00', await pg.inner_text('[data-heure]') == '08:03' and
             (await pg.inner_text('.texte')).replace(' ', ' ') == CORPUS['creneaux']['08:00']['lignes'][0])
        await ctx.close()
        # B · partage commencé à 03:19:50, terminé après le changement de créneau
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); pg = await ctx.new_page()
        await ctx.grant_permissions(['clipboard-read', 'clipboard-write']); await pg.clock.install(time='2026-11-16T03:19:50')
        await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"'); await pg.clock.run_for(200)
        await pg.click('[data-partager]'); await pg.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
        await pg.clock.run_for(25_000)
        derriere = (await pg.inner_text('[data-heure]'), await pg.inner_text('.mot'))
        await pg.click('[data-copier]'); copie = await pg.evaluate('navigator.clipboard.readText()')
        carte = await pg.evaluate('ChronoActions.dernier.carte.then(x=>x.mesures)')
        test('partage commencé à 03:19:50 : l’écran passe à 03:20 (Étale) pendant l’envoi', derriere == ('03:20', 'Étale'), str(derriere))
        fige = (await pg.inner_text('[data-fige]')).replace('\u00a0', ' ').replace('\u202f', ' ')
        test('… le lien copié après le changement reste celui de 03:19 et de la phrase témoin, citée en entier', copie == U + '/m/0319-a1'
             and fige == '03:19 · « Quelqu’un voudrait que cette minute passe. Quelqu’un voudrait qu’elle dure. »', f'{copie} · {fige}')
        test('… et la carte reste celle de 03:19, phrase témoin en deux blocs séparés par un blanc', carte['heure'] == '03:19' and len(carte['blocs']) >= 2
             and ' '.join(carte['blocs'][0]['lignes']).replace(' ', ' ') == 'Quelqu’un voudrait que cette minute passe.' and carte['blocs'][1]['avant'] >= 0.5 * carte['blocs'][1]['interligne'])
        async with pg.expect_download() as dl: await pg.click('[data-image]')
        f = await dl.value; chemin = await f.path()
        test('sur ordinateur, « Enregistrer l’image » télécharge la carte 1080 × 1350', Image.open(chemin).size == (1080, 1350) and f.suggested_filename == 'chronographe-la-03h19.png')
        await ctx.close()
        # C · page reçue : la phrase témoin en deux blocs ; aide à l'ajout distincte de « À propos »
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, user_agent=UA['iphone-safari']); pg = await ctx.new_page()
        await pg.goto(U + '/m/0317-a1/'); await pg.wait_for_load_state('networkidle')
        test('page reçue de 03:17 : deux blocs, « …cette minute passe. » / « Quelqu’un voudrait qu’elle dure. »',
             await pg.eval_on_selector_all('.fragment .texte', 'e=>e.map(x=>x.textContent)') == ['Quelqu’un voudrait que cette minute passe.', 'Quelqu’un voudrait qu’elle dure.'])
        ecart = await pg.evaluate("""(()=>{ const t=[...document.querySelectorAll('.fragment .texte')], lh=parseFloat(getComputedStyle(t[0]).lineHeight);
            return {blanc: t[1].getBoundingClientRect().top - t[0].getBoundingClientRect().bottom, ligne: lh}; })()""")
        test('… avec une respiration visible entre les deux blocs (au moins une demi-ligne de blanc)', ecart['blanc'] >= 0.5 * ecart['ligne'], f"blanc {ecart['blanc']:.0f} px, ligne {ecart['ligne']:.0f} px")
        await pg.click('[data-decouvrir]'); await pg.wait_for_timeout(600); await pg.click('[data-ajouter]')
        texte = await pg.inner_text('#d-ajout .corps')
        test('page reçue : « Ajouter à mon écran d’accueil » ouvre une vraie aide (iPhone, Safari), distincte de « À propos »',
             'Sur l’écran d’accueil' in texte and 'ouvrir le Chronographe' in texte and not await pg.evaluate('document.getElementById("d-propos").open'))
        await ctx.close()
        attendus = {'iphone-safari': ('ios-safari', 'Sur l’écran d’accueil'), 'iphone-chrome': ('ios-autre', 'Sur l’écran d’accueil'), 'iphone-instagram': ('ios-appli', 'Ouvrir dans Safari'),
                    'android-chrome': ('android-chrome', 'Ajouter à l’écran d’accueil'), 'android-samsung': ('android-samsung', 'Écran d’accueil'),
                    'mac-safari': ('mac-safari', 'Ajouter au Dock'), 'bureau-firefox': ('bureau-firefox', 'favoris')}
        bons = []
        for nom, (cle, mot) in attendus.items():
            ctx = await b.new_context(user_agent=UA[nom], viewport={'width': 400, 'height': 800}); pg = await ctx.new_page()
            await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"'); await pg.click('[data-ajouter]')
            if await pg.get_attribute('#d-ajout .corps', 'data-plateforme') == cle and mot in await pg.inner_text('#d-ajout .corps'): bons.append(nom)
            await ctx.close()
        test('aide à l’ajout adaptée : iPhone (Safari, Chrome, appli Instagram), Android (Chrome, Samsung), Mac Safari, Firefox', len(bons) == len(attendus), ', '.join(sorted(set(attendus) - set(bons))))
        # D · installation directe quand le navigateur la propose (Chrome Android, Edge…)
        ctx = await b.new_context(user_agent=UA['android-chrome'], viewport={'width': 412, 'height': 915}); pg = await ctx.new_page()
        await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"')
        await pg.evaluate("""(()=>{ const e=new Event('beforeinstallprompt'); window.__invite=0; e.prompt=()=>{window.__invite++; return Promise.resolve();}; e.userChoice=Promise.resolve({outcome:'accepted'}); window.dispatchEvent(e); })()""")
        await pg.click('[data-ajouter]'); await pg.click('[data-installer]'); await pg.wait_for_timeout(200)
        test('Android : le bouton « Ajouter Le Chronographe LÀ » déclenche l’installation du navigateur', await pg.evaluate('window.__invite') == 1)
        await ctx.close()
        # E · manifeste, icônes, réouverture par l'icône
        ctx = await b.new_context(); pg = await ctx.new_page()
        await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"')
        man = await pg.evaluate("fetch('/manifest.webmanifest').then(r=>r.json())")
        tailles = {}
        for ic in man['icons']:
            im = Image.open(site / ic['src'].lstrip('/')); tailles[ic['src']] = im.size
        test('manifeste : nom, nom court, ouverture sur le Chronographe, plein écran, icônes 192 / 512 / masquable',
             man['name'] == 'Le Chronographe LÀ' and man['start_url'] == '/?source=icone' and man['scope'] == '/' and man['display'] == 'standalone'
             and all(tuple(map(int, ic['sizes'].split('x'))) == tailles[ic['src']] for ic in man['icons']) and any(ic['purpose'] == 'maskable' for ic in man['icons']))
        test('icône Apple 180 × 180 et titre sous l’icône déclarés dans les pages', Image.open(site / 'icones/apple-touch-icon.png').size == (180, 180)
             and 'apple-touch-icon' in (site / 'm/1257-a1/index.html').read_text() and 'apple-mobile-web-app-title' in (site / 'index.html').read_text())
        sw = await pg.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active)")
        test('service worker actif (réseau d’abord ; lecture hors connexion)', sw)
        await ctx.close()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page(); await pg.clock.install(time='2026-11-16T21:44:00')
        await pg.goto(U + '/?source=icone'); await pg.wait_for_function('document.body.dataset.pret==="1"'); await pg.clock.run_for(300)
        test('réouverture par l’icône : le Chronographe à l’heure de l’appareil (21:44, Dilection)', await pg.inner_text('[data-heure]') == '21:44' and await pg.inner_text('.mot') == 'Dilection')
        await ctx.close()
        ctx = await b.new_context(user_agent=UA['iphone-safari']); pg = await ctx.new_page()
        await ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true})")
        await pg.goto(U + '/m/1257-a1/'); await pg.wait_for_url(U + '/'); 
        test('iPhone : une icône enregistrée depuis une minute partagée rouvre le Chronographe, pas la minute', pg.url == U + '/')
        await ctx.close()
        await b.close()
    srv.shutdown()

# ---------------------------------------------------------------- 9 · accès réservé (simulation locale de Cloudflare Access)
def serveur_protege(racine):
    """Imite Cloudflare Access : sans cookie de session, toute adresse renvoie (302) vers une page de connexion
    sur une autre origine ; la connexion revient sur /cdn-cgi/access/authorized, qui pose le cookie et ramène à l'adresse demandée."""
    journal_req = []
    class Login(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query); retour = q.get('redirect', [''])[0]
            corps = (f'<!DOCTYPE html><title>Connexion</title><p>Accès réservé</p><a id="entrer" href="{U}/cdn-cgi/access/authorized?redirect='
                     f'{urllib.parse.quote(retour, safe="")}">Se connecter</a>').encode()
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(corps)
    class Site(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            chemin = urllib.parse.urlparse(self.path); connecte = 'CF_Authorization=ok' in (self.headers.get('Cookie') or '')
            journal_req.append((chemin.path, connecte))
            if chemin.path == '/cdn-cgi/access/authorized':
                retour = urllib.parse.parse_qs(chemin.query).get('redirect', ['/'])[0]
                self.send_response(302); self.send_header('Set-Cookie', 'CF_Authorization=ok; Path=/; HttpOnly; SameSite=Lax'); self.send_header('Location', retour); self.end_headers(); return
            if not connecte:
                self.send_response(302); self.send_header('Location', f'{L}/login?redirect=' + urllib.parse.quote(U + self.path, safe='')); self.end_headers(); return
            return super().do_GET()
    class Serveur(http.server.ThreadingHTTPServer):
        def handle_error(self, *a): pass
    s1 = Serveur(('127.0.0.1', 0), functools.partial(Site, directory=str(racine))); s2 = Serveur(('127.0.0.1', 0), Login)
    U = f'http://127.0.0.1:{s1.server_address[1]}'; L = f'http://localhost:{s2.server_address[1]}'
    for s in (s1, s2): threading.Thread(target=s.serve_forever, daemon=True).start()
    return (s1, s2), U, L, journal_req

async def acces(site):
    from playwright.async_api import async_playwright
    titre('9 · Accès réservé : simulation locale de la connexion (ne remplace pas les contrôles après hébergement ni les essais réels)')
    srvs, U, L, req = serveur_protege(site)
    async with async_playwright() as p:
        b = await __import__('navigateur').lancer(p)
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page()
        await pg.goto(U + '/m/0317-a1/'); await pg.wait_for_load_state('networkidle')
        test('sans session, un lien direct vers une minute mène à la page de connexion, sans le texte', pg.url.startswith(L + '/login') and 'Quelqu’un' not in await pg.content())
        await pg.click('#entrer'); await pg.wait_for_url(U + '/m/0317-a1/'); await pg.wait_for_load_state('networkidle')
        test('après connexion, le testeur arrive sur la minute demandée (03:17, phrase témoin)', await pg.inner_text('[data-heure]') == '03:17')
        await ctx.close()
        # profil persistant (Chrome refuse toute installation en navigation privée, ce qu'est un contexte de test ordinaire)
        with tempfile.TemporaryDirectory() as profil:
            try: ctx = await p.chromium.launch_persistent_context(profil, channel='chrome')
            except Exception: ctx = await p.chromium.launch_persistent_context(profil)
            pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await pg.goto(U + '/'); await pg.wait_for_url(L + '/login*'); await pg.click('#entrer'); await pg.wait_for_url(U + '/')
            await pg.wait_for_function('document.body.dataset.pret==="1"')
            actif = await pg.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active)")
            cdp = await ctx.new_cdp_session(pg)
            man = await cdp.send('Page.getAppManifest')
            test('le manifeste se charge derrière la connexion (demande avec identifiants : crossorigin="use-credentials")',
                 not man.get('errors') and '"Le Chronographe LÀ"' in (man.get('data') or '') and ('/manifest.webmanifest', True) in req and ('/manifest.webmanifest', False) not in req,
                 str(man.get('errors')))
            await pg.wait_for_timeout(500)
            try: erreurs = (await cdp.send('Page.getInstallabilityErrors')).get('installabilityErrors', [])
            except Exception as e: erreurs = [{'errorId': 'indisponible : ' + str(e)[:60]}]
            test('Chrome juge la version d’essai installable derrière la connexion (manifeste, icônes, service worker)', actif and not erreurs, str([e.get('errorId') for e in erreurs]))
            await ctx.clear_cookies()
            await pg.goto(U + '/?source=icone'); await pg.wait_for_load_state('networkidle')
            test('session expirée : la réouverture par l’icône redemande la connexion (le service worker ne contourne pas la protection)', pg.url.startswith(L + '/login'))
            await pg.click('#entrer'); await pg.wait_for_url(U + '/?source=icone'); await pg.wait_for_function('document.body.dataset.pret==="1"')
            test('… puis, une fois reconnecté, le Chronographe s’ouvre à l’heure de l’appareil', bool(re.fullmatch(r'\d\d:\d\d', await pg.inner_text('[data-heure]'))))
            await ctx.close()
        await b.close()
    for s in srvs: s.shutdown()

# ---------------------------------------------------------------- 6 · règles
def essai_corpus(modifs=(), invites=None):
    c = copy.deepcopy(CORPUS)
    if invites is not None: c['invites'] = invites
    for m in modifs: m(c)
    return c

def regles():
    titre('6 · Règles du corpus, de conservation et de statut')
    car = polices.caracteres(); n = CORPUS['creneaux'][LONG]
    v = lambda c, reg=None: CS.verifier_corpus(c, reg or {'textes': {}}, car)
    reg = {'textes': {'c1250-a@1': {'id': 'c1250-a', 'version': 1, 'empreinte': CS.empreinte(CS.contenu({**n, 'heure': LONG}))}}}
    c2 = essai_corpus([lambda c: c['creneaux'][LONG].update(definition=n['definition'].replace('rugueuse', 'rauque'))])
    _, e, _ = v(c2, reg); test('contenu publié modifié sans nouvelle version : refusé', any('version 2' in x for x in e))
    c2['creneaux'][LONG]['version'] = 2
    _, e, _ = v(c2, reg); test('même correction en version 2 : acceptée', not e)
    c3 = essai_corpus([lambda c: c['creneaux'][LONG].update(statut='autre_statut')])
    _, e, _ = v(c3, reg); test('changement de statut éditorial : aucune nouvelle version (le statut ne s’affiche pas)', not e)
    reg3 = copy.deepcopy(reg); reg3['textes']['c1250-a@2'] = {'id': 'c1250-a', 'version': 2, 'empreinte': 'x'}
    _, e, _ = v(CORPUS, reg3); test('retour à une version antérieure : refusé', any('reculer' in x for x in e))
    F = '03:30'
    cas = [
        ('créneau qui n’est pas un multiple de dix minutes : refusé', lambda c: c['creneaux'].update({'03:17': c['creneaux'].pop('03:10')}), 'clé invalide'),
        ('type inconnu : refusé', lambda c: c['creneaux'][F].update(type='citation'), 'type'),
        ('fragment de plus de 170 signes : refusé', lambda c: c['creneaux'][F].update(lignes=['x' * 171]), '171 signes'),
        ('définition de plus de 180 signes : refusée', lambda c: c['creneaux'][LONG].update(definition='x' * 181), '181 signes'),
        ('nom sans genre : refusé', lambda c: c['creneaux'][LONG].update(grammaire='Nom · Littérature'), 'genre attendu'),
        ('mot sans source : refusé', lambda c: c['creneaux'][LONG].update(sources=[]), 'source'),
        ('mot trop long pour la ligne du plus petit écran, sans césure : refusé', lambda c: c['creneaux'][LONG].update(mot='Anticonstitutionnellement'), 'U+00AD'),
        ('caractère absent de la police : refusé', lambda c: c['creneaux'][F].update(lignes=['Une ✶ minute.']), 'U+2736'),
        ('identifiant qui ne correspond pas au créneau : refusé', lambda c: c['creneaux'][LONG].update(id='c0330-a'), 'invalide'),
    ]
    for nom, m, attendu in cas:
        _, e, _ = v(essai_corpus([m])); test(nom, any(attendu in x for x in e), e[0][:110] if e else 'accepté')
    _, e, _ = v(essai_corpus([lambda c: c['creneaux'][F].update(attribution={'auteur': 'Nom d’essai'})])); test('attribution possible quand elle sera nécessaire (facultative)', not e)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); rp = t / 'r.json'; rp.write_text('{"textes":{}}')
        # un texte dont le statut n'est pas déclaré publiable (sources/config.json) bloque toute mise en ligne
        cp = t / 'c.json'; cp.write_text(json.dumps(essai_corpus([lambda c: c['creneaux'][F].update(statut='brouillon')]), ensure_ascii=False))
        try:
            with contextlib.redirect_stdout(io.StringIO()): CS.construire(t / 's', R / 'media', enregistrer=True, registre_p=rp, corpus_p=cp)
            refuse = False
        except CS.Erreur as x: refuse = 'statut' in str(x)
        test('mise en ligne (--enregistrer) refusée dès qu’un texte n’a pas un statut déclaré publiable', refuse and json.loads(rp.read_text()) == {'textes': {}})

ESSAI = {'id': 'c0320-i1', 'version': 1, 'type': 'mot', 'mot': 'Essai', 'grammaire': 'Nom masculin · Essai technique',
         'definition': 'Contenu invité de démonstration, jamais publié.', 'sources': [{'titre': 'Source d’essai', 'url': 'https://example.org/'}],
         'auteur': {'nom': 'Autrice d’essai'}, 'debut': '2027-03-01', 'fin': '2027-03-31'}

async def navigateur_invites(racine):
    from playwright.async_api import async_playwright
    srv, U = serveur(racine)
    async def ouvrir(b, quand, chemin='/'):
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page()
        await pg.clock.install(time=quand); await pg.goto(U + chemin); await pg.wait_for_load_state('networkidle'); await pg.clock.run_for(600)
        return ctx, pg
    async with async_playwright() as p:
        b = await __import__('navigateur').lancer(p)
        ctx, pg = await ouvrir(b, '2027-02-28T03:27:10'); test('la veille du début : contenu de base (Étale)', await pg.inner_text('.mot') == 'Étale'); await ctx.close()
        ctx, pg = await ouvrir(b, '2027-03-01T03:27:10'); txt = await pg.inner_text('[data-phrase]')
        test('pendant la période : le contenu invité remplace la base, avec son crédit', 'Essai' in txt and 'Autrice d’essai' in txt); await ctx.close()
        ctx, pg = await ouvrir(b, '2027-04-01T03:27:10'); test('après l’échéance : la base reprend seule sa place', await pg.inner_text('.mot') == 'Étale'); await ctx.close()
        ctx, pg = await ouvrir(b, '2028-01-01T10:00:00', '/m/0327-i1-v1/')
        test('contenu invité partagé, ouvert après l’échéance : texte et crédit d’origine', 'Autrice d’essai' in await pg.inner_text('[data-phrase]')); await ctx.close()
        await b.close()
    srv.shutdown()

def invites(t):
    titre('7 · Contenus invités (structure prête, données d’essai jamais enregistrées)')
    car = polices.caracteres()
    def essai(*modifs): return CS.verifier_corpus(essai_corpus(modifs, {'03:20': [copy.deepcopy(ESSAI)]}), {'textes': {}}, car)
    textes, e, _ = essai(); test('contenu invité valide : accepté, identifiant distinct (c0320-i1 / c0320-a)', not e and 'c0320-i1@1' in textes, '; '.join(e))
    _, e, _ = essai(lambda c: c['invites']['03:20'].append({**ESSAI, 'id': 'c0320-i2', 'debut': '2027-03-20', 'fin': '2027-04-10'}))
    test('deux invitations qui se chevauchent : refusé', any('chevauchent' in x for x in e))
    # site réduit : le créneau de l'invitation seulement
    c = essai_corpus(invites={'03:20': [copy.deepcopy(ESSAI)]}); c['creneaux'] = {'03:20': c['creneaux']['03:20']}
    cp, rp = t / 'corpus-i.json', t / 'registre-i.json'; cp.write_text(json.dumps(c, ensure_ascii=False)); rp.write_text('{"textes":{}}')
    with contextlib.redirect_stdout(io.StringIO()): CS.construire(t / 'site-invites', R / 'media', corpus_p=cp, registre_p=rp)
    asyncio.run(navigateur_invites(t / 'site-invites'))

def main():
    a = argparse.ArgumentParser(); a.add_argument('--rapport')
    a.add_argument('--acces-reserve', action='store_true', help='vérifier la construction destinée à l’hébergement protégé (bandeau « accès réservé »)')
    o = a.parse_args(); debut = time.time()
    corpus(); r = rythme()
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); titre('Construction d’essai (aucune publication, registre intact)')
        reg_avant = (R / 'sources/corpus/registre.json').read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            CS.construire(t / 'site', R / 'media', acces_reserve=o.acces_reserve); r2 = CS.construire(t / 'site', R / 'media', acces_reserve=o.acces_reserve)
        test('construction reproductible : la seconde passe ne crée ni ne remplace rien', r2['fichiers_crees'] == 0 and not r2['fichiers_remplaces'])
        test('registre non modifié par un essai', (R / 'sources/corpus/registre.json').read_bytes() == reg_avant)
        partage(t / 'site', r)
        asyncio.run(affichage(t / 'site'))
        asyncio.run(cartes(t / 'site'))
        asyncio.run(parcours(t / 'site'))
        asyncio.run(acces(t / 'site'))
        regles(); invites(t)
    bilan = f'{len(ok)} vérifications réussies, {len(ko)} en échec ({round((time.time() - debut) / 60, 1)} min)'
    print('\n' + bilan)
    if o.rapport:
        pathlib.Path(o.rapport).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(o.rapport).write_text('# Le Chronographe LÀ — contrôles sur le corpus complet\n\n'
            f'Corpus : {CORPUS["edition"]} · 144 contenus (72 mots, 72 fragments) · construction : {"version d’essai — accès réservé" if o.acces_reserve else "essai local"} · contrôles automatisés uniquement (les essais sur appareils réels sont consignés dans ESSAIS-TELEPHONES.md).\n' + '\n'.join(journal) + f'\n\n**{bilan}**\n')
    sys.exit(1 if ko else 0)

if __name__ == '__main__': main()
