"""
Le Chronographe LÀ — captures de contrôle, prises sur une construction donnée (par défaut la copie d’essai GitHub Pages, servie sous son sous-chemin).

    python3 outils/capturer.py [--site ../essai-github] [--chemin /chronographe-la-essai] [--sortie controles/captures]

Chaque capture est prise dans Chrome sur le dossier exact qui sera hébergé : le Chronographe, la page reçue,
la fenêtre de partage, et les images à enregistrer obtenues par le vrai bouton « Enregistrer l’image ».
Le fichier PROVENANCE.txt indique la construction d'origine (version du service worker, empreintes des pages).
Le script s'arrête si la phrase témoin n'apparaît pas en deux blocs, sur la page reçue comme sur la carte.
"""
import argparse, asyncio, datetime, hashlib, pathlib, re, shutil, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from verifier import serveur, UA            # même serveur local et mêmes navigateurs que les contrôles

R = pathlib.Path(__file__).resolve().parents[1]
TEMOIN = ['Quelqu’un voudrait que cette minute passe.', 'Quelqu’un voudrait qu’elle dure.']

async def capturer(site, sortie, chemin=''):
    from playwright.async_api import async_playwright
    import navigateur
    racine = site
    if chemin:   # copie GitHub Pages : servie sous son sous-chemin, comme à <compte>.github.io/<projet>/
        racine = pathlib.Path(tempfile.mkdtemp()); (racine / chemin.strip('/')).symlink_to(site, target_is_directory=True)
    srv, U = serveur(racine); U += chemin; faites = []
    async def page(b, w, h, quand, ua=None):
        ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, reduced_motion='reduce', **({'user_agent': UA[ua]} if ua else {}))
        pg = await ctx.new_page(); await pg.clock.install(time=quand); return ctx, pg
    async with async_playwright() as p:
        b = await navigateur.lancer(p)
        # 1 · le Chronographe (page d'accueil), à 03:17 et 12:57
        for quand, nom, w, h in [('2026-11-16T03:17:20', 'chronographe-0317-390x844', 390, 844), ('2026-11-16T12:57:20', 'chronographe-1257-1440x900', 1440, 900)]:
            ctx, pg = await page(b, w, h, quand, 'iphone-safari' if w < 500 else None)
            await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"'); await pg.clock.run_for(600)
            if '0317' in nom:
                blocs = await pg.eval_on_selector_all('.fragment .texte', 'e=>e.map(x=>x.textContent)')
                if blocs != TEMOIN: sys.exit(f'ARRÊT : le Chronographe n’affiche pas la phrase témoin en deux blocs ({blocs})')
            await pg.screenshot(path=str(sortie / f'{nom}.png')); faites.append(nom)
            if '0317' in nom:   # la fenêtre « Partager cet instant »
                await pg.click('[data-partager]'); await pg.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
                await pg.wait_for_timeout(300); await pg.screenshot(path=str(sortie / 'partage-0317-390x844.png')); faites.append('partage-0317-390x844')
            await ctx.close()
        # 2 · pages reçues
        for adr, quand, nom, w, h in [('/m/0317-a1/', '2026-11-16T09:12:00', 'reception-temoin-0317-390x844', 390, 844),
                                         ('/m/1257-a1/', '2026-11-17T08:03:10', 'reception-synesthesie-390x844', 390, 844),
                                         ('/m/1657-a1/', '2026-11-16T10:00:00', 'reception-aparte-1440x900', 1440, 900),
                                         ('/m/2217-a1/', '2026-11-16T10:00:00', 'reception-evanescent-320x568', 320, 568)]:
            ctx, pg = await page(b, w, h, quand, 'iphone-safari' if w < 500 else None)
            await pg.goto(U + adr); await pg.wait_for_load_state('networkidle'); await pg.clock.run_for(600)
            if '0317' in adr:
                blocs = await pg.eval_on_selector_all('.fragment .texte', 'e=>e.map(x=>x.textContent)')
                if blocs != TEMOIN: sys.exit(f'ARRÊT : la page reçue n’affiche pas la phrase témoin en deux blocs ({blocs})')
            await pg.screenshot(path=str(sortie / f'{nom}.png')); faites.append(nom)
            await ctx.close()
        # 3 · images à enregistrer, par le vrai bouton (ordinateur : téléchargement)
        for quand in ['00:07', '03:17', '03:47', '08:17', '12:57', '16:57']:
            ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce', accept_downloads=True); pg = await ctx.new_page()
            await pg.clock.install(time=f'2026-11-16T{quand}:20'); await pg.goto(U + '/'); await pg.wait_for_function('document.body.dataset.pret==="1"')
            await pg.click('[data-partager]'); await pg.wait_for_function('document.getElementById("d-partage").dataset.pret==="1"')
            if quand == '03:17':
                m = await pg.evaluate('ChronoActions.dernier.carte.then(x=>x.mesures)')
                premier = ' '.join(m['blocs'][0]['lignes']).replace(' ', ' ')
                if premier != TEMOIN[0]: sys.exit(f'ARRÊT : la carte ne sépare pas la phrase témoin ({premier})')
            async with pg.expect_download() as dl: await pg.click('[data-image]')
            nom = 'carte-' + quand.replace(':', ''); await (await dl.value).save_as(str(sortie / f'{nom}.png')); faites.append(nom)
            await ctx.close()
        await b.close()
    srv.shutdown()
    return faites

def main():
    a = argparse.ArgumentParser(); a.add_argument('--site', default=str(R.parent / 'essai-github')); a.add_argument('--chemin', default='/chronographe-la-essai')
    a.add_argument('--sortie', default=str(R / 'controles' / 'captures'))
    o = a.parse_args(); site = pathlib.Path(o.site).resolve(); sortie = pathlib.Path(o.sortie); chemin = ('/' + o.chemin.strip('/')) if o.chemin.strip('/') else ''
    if not (site / 'index.html').exists(): sys.exit(f'ARRÊT : aucune construction dans {site} (python3 outils/construire_site.py --acces-reserve)')
    sortie.mkdir(parents=True, exist_ok=True)
    faites = asyncio.run(capturer(site, sortie, chemin))
    version = re.search(r"CACHE = PREFIXE \+ '([0-9a-f]+)'", (site / 'sw.js').read_text()).group(1)
    emp = lambda f: hashlib.sha256((site / f).read_bytes()).hexdigest()[:16]
    bandeau = re.search(r'<p class="essai">([^<]*)', (site / 'index.html').read_text())
    (sortie / 'PROVENANCE.txt').write_text(
        f'Captures prises le {datetime.datetime.now():%Y-%m-%d %H:%M} dans Chrome, sur la construction {site.name}' + (f', servie sous {chemin}/' if chemin else '') + '\n'
        f'Version de la construction (service worker) : {version}\n'
        f'Bandeau : {bandeau.group(1) if bandeau else "(aucun)"}\n'
        f'Empreintes : index.html {emp("index.html")} · m/0317-a1/index.html {emp("m/0317-a1/index.html")} · commun/carte.js {emp("commun/carte.js")}\n'
        f'Fichiers : {", ".join(f + ".png" for f in faites)}\n'
        'Les cartes sont les fichiers téléchargés par le bouton « Enregistrer l’image » (ordinateur), pas des reconstitutions.\n')
    print(f'{len(faites)} captures · construction {version} · {sortie}')

if __name__ == '__main__': main()
