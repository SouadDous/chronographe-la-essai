"""
Le Chronographe LÀ — essai automatique de la formule « page Squarespace + copie GitHub Pages ».

    python3 outils/essayer_integration.py [--site ../essai-github] [--chemin /chronographe-la-essai] [--rapport controles/rapport-integration.md]

Reproduit en local, dans Chrome :
  · l'origine <compte>.github.io, avec le Chronographe servi sous son sous-chemin, et, sur la même origine,
    un « ancien Chronographe » factice (/chronographe/) qui garde ses propres données ;
  · une page de site tiers (autre origine, comme une page Squarespace) qui affiche le Chronographe dans un cadre
    (<iframe allow="web-share; clipboard-write">), comme le ferait un bloc Code.
Ce sont des contrôles automatisés : ils ne remplacent pas les essais sur de vrais téléphones.
"""
import argparse, asyncio, functools, http.server, pathlib, re, shutil, sys, tempfile, threading, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from verifier import test, titre, ok, ko, UA

R = pathlib.Path(__file__).resolve().parents[1]
TEMOIN = ['Quelqu’un voudrait que cette minute passe.', 'Quelqu’un voudrait qu’elle dure.']

ANCIEN = """<!DOCTYPE html><meta charset="utf-8"><title>Ancien Chronographe (factice)</title><p>ancien</p>
<script>caches.open('chronographe-v1').then(c=>c.put('/chronographe/ancien.txt', new Response('ancien'))).then(()=>{localStorage.setItem('chronographe','ancien');document.title='pret';});</script>"""

def page_hote(src, hauteur='100svh'):
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Éditions LÀ — page non liée (simulation Squarespace)</title>
<style>body{{margin:0;font:16px Georgia,serif}} header{{height:64px;display:flex;align-items:center;padding:0 16px;border-bottom:1px solid #ddd}}
.bloc-code iframe{{display:block;width:100%;height:{hauteur};border:0}} footer{{padding:24px 16px}}</style></head>
<body><header>Éditions LÀ</header><div class="bloc-code">
<iframe id="chrono" src="{src}" title="Le Chronographe LÀ — version d’essai" allow="web-share; clipboard-write" loading="eager"></iframe>
</div><footer>Pied de page du site</footer></body></html>"""

def servir(racine, hote='127.0.0.1'):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    class S(http.server.ThreadingHTTPServer):
        def handle_error(self, *a): pass
    s = S((hote, 0), functools.partial(H, directory=str(racine))); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f'http://{"localhost" if hote == "127.0.0.1" and False else hote}:{s.server_address[1]}'

async def essais(site, chemin):
    from playwright.async_api import async_playwright
    import navigateur
    t = pathlib.Path(tempfile.mkdtemp())
    gh = t / 'github'; (gh / chemin.strip('/')).parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(site, gh / chemin.strip('/')); (gh / 'chronographe').mkdir(); (gh / 'chronographe' / 'index.html').write_text(ANCIEN)
    s1, G = servir(gh)                                   # « souaddous.github.io »
    G = G + chemin                                       # adresse autonome du Chronographe
    hote = t / 'squarespace'; hote.mkdir()
    s2 = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(type('H', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *a: None}), directory=str(hote)))
    threading.Thread(target=s2.serve_forever, daemon=True).start()
    Q = f'http://localhost:{s2.server_address[1]}'       # autre origine, comme www.editionsla.com
    (hote / 'essai.html').write_text(page_hote(G + '/'))
    (hote / 'essai-0317.html').write_text(page_hote(G + '/m/0317-a1/'))
    async with async_playwright() as p:
        b = await navigateur.lancer(p)

        titre('A · Adresse autonome, sous le sous-chemin du projet (essais à faire en ouvrant directement cette adresse)')
        with tempfile.TemporaryDirectory() as profil:
            try: ctx = await p.chromium.launch_persistent_context(profil, channel='chrome', viewport={'width': 390, 'height': 844}, accept_downloads=True)
            except Exception: ctx = await p.chromium.launch_persistent_context(profil, viewport={'width': 390, 'height': 844}, accept_downloads=True)
            pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await pg.goto(G.rsplit(chemin, 1)[0] + '/chronographe/'); await pg.wait_for_function('document.title==="pret"')
            erreurs = []; pg.on('response', lambda r: erreurs.append(r.url) if r.status >= 400 else None)
            await pg.clock.install(time='2026-11-16T12:57:20'); await pg.goto(G + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"')
            test('le Chronographe s’ouvre sous le sous-chemin, sans aucune ressource manquante', await pg.inner_text('[data-heure]') == '12:57' and not erreurs, ', '.join(erreurs[:3]))
            await pg.click('[data-partager]'); await pg.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
            lien = await pg.input_value('[data-lien]')
            test('« Partager cet instant » donne l’adresse autonome de la minute', lien == G + '/m/1257-a1', lien)
            await pg.goto(G + '/m/0317-a1/'); await pg.wait_for_load_state('networkidle')
            test('la page reçue 03:17 s’ouvre, phrase témoin en deux blocs', await pg.eval_on_selector_all('.fragment .texte', 'e=>e.map(x=>x.textContent)') == TEMOIN)
            await pg.click('[data-decouvrir]') if await pg.query_selector('[data-decouvrir]') else await pg.click('text=Découvrir')
            await pg.wait_for_timeout(800)
            test('« Ouvrir le Chronographe » reste dans le projet', pg.url.startswith(G + '/'), pg.url)
            await pg.goto(G + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"')
            portee = await pg.evaluate('navigator.serviceWorker.ready.then(r=>r.scope)')
            test('le service worker ne couvre que le projet', portee == G + '/', portee)
            cdp = await ctx.new_cdp_session(pg); man = await cdp.send('Page.getAppManifest')
            import json as J; m = J.loads(man.get('data') or '{}')
            test('manifeste : identité, démarrage et portée propres au projet (distincts de l’ancien Chronographe)',
                 not man.get('errors') and m.get('id') == chemin + '/' and m.get('scope') == chemin + '/' and m.get('start_url') == chemin + '/?source=icone')
            await pg.wait_for_timeout(500)
            inst = (await cdp.send('Page.getInstallabilityErrors')).get('installabilityErrors', [])
            test('Chrome juge le Chronographe installable à son adresse autonome', not inst, str([e.get('errorId') for e in inst]))
            anciens = await pg.evaluate("Promise.all([caches.keys(), caches.open('chronographe-v1').then(c=>c.match('/chronographe/ancien.txt')).then(r=>r&&r.text())]).then(([k,v])=>({k,v,ls:localStorage.getItem('chronographe')}))")
            test('les données de l’ancien Chronographe (même origine) sont intactes', anciens['v'] == 'ancien' and anciens['ls'] == 'ancien' and 'chronographe-v1' in anciens['k'], str(anciens['k']))
            await ctx.set_offline(True); await pg.goto(G + '/?source=icone'); await pg.wait_for_function('document.body.dataset.pret==="1"')
            test('réouverture « par l’icône » hors connexion : le Chronographe s’affiche', bool(re.fullmatch(r'\d\d:\d\d', await pg.inner_text('[data-heure]'))))
            await ctx.set_offline(False); await ctx.close()

        titre('B · Dans une page d’un autre site (simulation d’une page Squarespace avec un bloc Code)')
        for w, h, ua, nom in [(390, 844, 'android-chrome', 'téléphone'), (1440, 900, None, 'ordinateur')]:
            ctx = await b.new_context(viewport={'width': w, 'height': h}, accept_downloads=True, **({'user_agent': UA[ua]} if ua else {}))
            await ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=G.rsplit(chemin, 1)[0])
            pg = await ctx.new_page(); await pg.clock.install(time='2026-11-16T12:59:40')
            await pg.goto(Q + '/essai.html'); f = pg.frame_locator('#chrono'); fr = pg.frame(url=re.compile(re.escape(G)))
            await fr.wait_for_function('document.body.dataset.pret==="1"')
            v = await fr.evaluate("(()=>{const v=document.querySelector('video');return v?{src:v.currentSrc||v.src,poster:!!v.poster}:null})()")
            test(f'{nom} : le Chronographe s’affiche dans la page, avec la sphère', await fr.inner_text('[data-heure]') == '12:59' and v is not None, str(v))
            cibles = await fr.eval_on_selector_all('a[href^="http"]', 'e=>e.filter(a=>a.host!==location.host).map(a=>a.target)')
            test(f'{nom} : les liens vers le site Éditions LÀ s’ouvrent à la place de la page, pas dans le cadre', cibles and all(c == '_top' for c in cibles), str(cibles))
            avant = await fr.inner_text('.phrase'); await pg.clock.run_for(25_000); await pg.wait_for_timeout(1500)
            test(f'{nom} : le changement de rencontre a lieu à 13:00 dans la page', await fr.inner_text('[data-heure]') == '13:00' and await fr.inner_text('.phrase') != avant)
            await pg.screenshot(path=str(R / 'controles' / 'captures' / f'squarespace-simulation-{"telephone" if w < 500 else "ordinateur"}.png'))
            cadre = await pg.evaluate("(()=>{const r=document.getElementById('chrono').getBoundingClientRect();return {h:r.height,w:r.width}})()")
            deborde = await fr.evaluate('document.documentElement.scrollHeight > innerHeight + 2')
            test(f'{nom} : la composition tient dans le cadre ({cadre["w"]:.0f} × {cadre["h"]:.0f})', not deborde or w < 400)
            await f.locator('[data-partager]').click(); await fr.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
            lien = await fr.input_value('[data-lien]')
            test(f'{nom} : « Partager » dans la page donne l’adresse autonome de la minute (13:00), pas la page du site', lien == G + '/m/1300-a1', lien)
            await f.locator('[data-copier]').click(); await pg.wait_for_timeout(300)
            test(f'{nom} : « Copier le lien » fonctionne dans la page', 'copié' in await fr.inner_text('[data-statut]'))
            async with pg.expect_download() as dl: await f.locator('[data-image]').click()
            test(f'{nom} : « Enregistrer l’image » fonctionne dans la page (téléchargement)', (await dl.value).suggested_filename == 'chronographe-la-13h00.png')
            await f.locator('#d-partage .fermer').click()
            await f.locator('[data-ajouter]').click()
            plat = await fr.get_attribute('#d-ajout .corps', 'data-plateforme'); cible = await fr.get_attribute('#d-ajout [data-autonome]', 'href')
            test(f'{nom} : « Ajouter à mon écran d’accueil » dans la page renvoie vers l’adresse autonome (l’ajout depuis la page installerait la page du site)',
                 plat == 'integre' and cible == chemin + '/', f'{plat} {cible}')
            await ctx.close()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page()
        await pg.goto(Q + '/essai-0317.html'); fr = pg.frame(url=re.compile(re.escape(G))); await fr.wait_for_load_state('networkidle')
        test('une minute reçue (03:17) s’affiche aussi dans la page, en deux blocs', await fr.eval_on_selector_all('.fragment .texte', 'e=>e.map(x=>x.textContent)') == TEMOIN)
        await ctx.close(); await b.close()
    s1.shutdown(); s2.shutdown(); shutil.rmtree(t, ignore_errors=True)

def main():
    a = argparse.ArgumentParser(); a.add_argument('--site', default=str(R.parent / 'essai-github')); a.add_argument('--chemin', default='/chronographe-la-essai')
    a.add_argument('--rapport'); o = a.parse_args(); debut = time.time()
    asyncio.run(essais(pathlib.Path(o.site).resolve(), '/' + o.chemin.strip('/')))
    print(f'\n{len(ok)} vérifications réussies, {len(ko)} en échec ({(time.time() - debut) / 60:.1f} min)')
    if o.rapport:
        pathlib.Path(o.rapport).write_text('# Essai automatique : page Squarespace + copie GitHub Pages (simulation locale)\n\n'
            'Contrôles automatisés dans Chrome ; ils ne remplacent pas les essais sur de vrais téléphones.\n\n'
            + ''.join(f'- ✓ {x}\n' for x in ok) + ''.join(f'- ✗ {x}\n' for x in ko) + f'\n{len(ok)} réussies, {len(ko)} en échec.\n')
    sys.exit(1 if ko else 0)

if __name__ == '__main__': main()
