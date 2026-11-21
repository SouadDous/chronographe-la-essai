"""
Le Chronographe LÀ — régénération des visuels à partir d'une animation de la sphère.

    python3 outils/generer.py chemin/vers/animation.mp4 [--image 30] [--fondu 30] [--sortie exports/<nom>] [--adopter]

L'animation d'origine n'est jamais modifiée. Produit, dans le dossier de sortie :
  media/   la boucle web fondue (624 px), la boucle de pastille (208 px), les versions « plus lentes »
           interpolées, l'image fixe (mouvement réduit, aperçus, cartes) en 624 et 208 px ;
  minute-partagee-1080x1350.png   l'image à enregistrer pour 03:17, avec le contenu d'essai de son créneau et les textes validés ;
  apercu-lien-1200x630.jpg        l'aperçu de lien (JPEG sous 300 Ko) ;
  releve.json                     raccord de boucle, rythme, poids des fichiers.
--adopter copie ensuite media/ dans le dossier media/ du projet, utilisé par construire_site.py.
Sans ce drapeau, rien d'autre n'est touché : on peut comparer plusieurs animations côte à côte.
"""
import argparse, json, pathlib, shutil, subprocess, sys, asyncio, threading, http.server, functools, io
import numpy as np
from PIL import Image

R = pathlib.Path(__file__).resolve().parents[1]
S = R / 'sources'
sys.path.insert(0, str(R / 'outils'))

def lire(src):
    w, h = map(int, subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',src],capture_output=True,text=True).stdout.strip().split(','))
    raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,h,w,3), w, h

def mouvement(F):
    d = [np.abs(F[(i+1)%len(F)].astype(np.float32)-F[i]).mean() for i in range(len(F))]
    return d[:-1], d[-1]

def encoder(F, dst, taille, crf, extra_vf=''):
    n, h, w, _ = F.shape
    vf = (extra_vf + ',' if extra_vf else '') + f'scale={taille}:{taille}:flags=lanczos'
    p = subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','24','-i','-','-vf',vf,
        '-c:v','libx264','-preset','veryfast','-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart','-an',str(dst)],stdin=subprocess.PIPE)
    p.stdin.write(F.tobytes()); p.stdin.close(); p.wait()

def main():
    a = argparse.ArgumentParser(); a.add_argument('video'); a.add_argument('--image', type=int, default=30)
    a.add_argument('--fondu', type=int, default=30); a.add_argument('--sortie'); a.add_argument('--adopter', action='store_true')
    o = a.parse_args()
    S_ = pathlib.Path(o.sortie) if o.sortie else R / 'exports' / pathlib.Path(o.video).stem
    M = S_ / 'media'; M.mkdir(parents=True, exist_ok=True)
    F, w, h = lire(o.video); N = len(F); K = o.fondu
    d, raccord = mouvement(F)
    rel = {'source': pathlib.Path(o.video).name, 'format': f'{w}×{h}', 'images': N, 'duree_s': round(N/24,2),
           'raccord_original_sur_mouvement_moyen': round(float(raccord/np.mean(d)),1),
           'rythme_premiere_moitie': round(float(np.mean(d[:N//2])),2), 'rythme_seconde_moitie': round(float(np.mean(d[N//2:])),2),
           'image_fixe': o.image, 'fondu_images': K}
    # boucle fondue : les K dernières images se fondent dans les K premières (courbe douce)
    out = []
    for t in range(N-K):
        if t < K:
            x = t/K; x = x*x*(3-2*x); out.append(F[N-K+t].astype(np.float32)*(1-x) + F[t].astype(np.float32)*x)
        else: out.append(F[t].astype(np.float32))
    B = np.clip(np.stack(out),0,255).astype(np.uint8)
    db, rb = mouvement(B)
    rel.update({'boucle_s': round(len(B)/24,2), 'raccord_boucle_sur_mouvement_moyen': round(float(rb/np.mean(db)),2)})
    encoder(B, M/'b-624.mp4', 624, 23); encoder(B, M/'b-208.mp4', 208, 24)
    # version plus lente (images intermédiaires calculées), sur deux tours pour lisser aussi le raccord
    tmp = S_/'_double.mp4'; encoder(np.concatenate([B,B]), tmp, w, 18)
    raw = subprocess.run(['ffmpeg','-v','error','-i',str(tmp),'-vf','setpts=1.35*PTS,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    L2 = np.frombuffer(raw,np.uint8).reshape(-1,h,w,3); L = len(L2)//2; Lb = L2[L//2:L//2+L]
    encoder(Lb, M/'b-lent-624.mp4', 624, 23); encoder(Lb, M/'b-lent-208.mp4', 208, 24); tmp.unlink()
    im = Image.fromarray(B[min(o.image, len(B)-1)]).resize((624,624), Image.LANCZOS)
    im.save(M/'b-fixe.jpg', quality=90); im.resize((208,208), Image.LANCZOS).save(M/'b-fixe-208.jpg', quality=88)
    asyncio.run(rendre(M, S_))
    for f in sorted(M.iterdir()) + [S_/'minute-partagee-1080x1350.png', S_/'apercu-lien-1200x630.jpg']:
        rel['poids_'+f.name] = f'{round(f.stat().st_size/1024)} Ko'
    (S_/'releve.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1)); print(json.dumps(rel, ensure_ascii=False, indent=1))
    if o.adopter:
        for f in M.iterdir(): shutil.copy(f, R/'media'/f.name)
        print('médias adoptés dans', R/'media')

async def rendre(M, S_):
    """Rendu des deux visuels de partage avec les gabarits du site (mêmes styles que les pages publiées)."""
    from playwright.async_api import async_playwright
    import tempfile
    cfg = json.loads((S/'config.json').read_text()); corpus = json.loads((S/'corpus'/'corpus.json').read_text())
    temoin = corpus['creneaux']['03:10']   # le contenu du créneau de 03:17, la minute de démonstration du partage
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); (t/'commun'/'polices').mkdir(parents=True); shutil.copytree(M, t/'commun'/'media')
        shutil.copy(S/'gabarits'/'commun.css', t/'commun'); shutil.copy(S/'gabarits'/'rendu.html', t); shutil.copy(S/'scripts'/'carte.js', t/'commun')
        for f in ['ebg-roman.woff2','ebg-italic.woff2']: shutil.copy(S/'polices'/f, t/'commun'/'polices')
        class Silencieux(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
        srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Silencieux, directory=str(t)))
        threading.Thread(target=srv.serve_forever, daemon=True).start(); U = f'http://127.0.0.1:{srv.server_address[1]}/rendu.html#'
        carte = json.dumps({'heure': '03:17', 'notice': temoin, 'promesse': cfg['promesse'], 'invitation': cfg['invitation'],
                            'adresse': cfg['adresse_ecrite']}, ensure_ascii=False)
        async with async_playwright() as p:
            b = await __import__('navigateur').lancer(p); pg = await b.new_page(viewport={'width':1200,'height':1400})
            await pg.goto(U+'carte/'+__import__('urllib.parse').parse.quote(carte)); await pg.wait_for_function('document.body.dataset.pret==="1"')
            # la carte est dessinée par carte.js (le même code que sur le téléphone) : on enregistre le PNG qu'il produit
            png_carte = await pg.evaluate("document.querySelector('#r canvas').toDataURL('image/png').split(',')[1]")
            (S_/'minute-partagee-1080x1350.png').write_bytes(__import__('base64').b64decode(png_carte))
            await pg.goto(U+'og/03:17'); await pg.reload(); await pg.wait_for_function('document.body.dataset.pret==="1"')
            png = await pg.locator('#r').screenshot()
            await b.close()
        srv.shutdown()
    im = Image.open(io.BytesIO(png)).convert('RGB'); q = 90
    while True:   # sous 300 Ko : seuil le plus strict signalé (WhatsApp)
        im.save(S_/'apercu-lien-1200x630.jpg', quality=q, optimize=True, progressive=True)
        if (S_/'apercu-lien-1200x630.jpg').stat().st_size < 300*1024 or q <= 60: break
        q -= 5

if __name__ == '__main__': main()
