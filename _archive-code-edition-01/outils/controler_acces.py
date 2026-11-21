"""
Le Chronographe LÀ — contrôle de la protection de la copie hébergée, depuis un navigateur « non connecté ».

    python3 outils/controler_acces.py https://chronographe-la-essai.pages.dev [--attente]

Aucune dépendance (Python 3 seul). Demande, sans cookie ni identifiant, chaque type d'adresse du projet :
adresse principale, Chronographe, minutes partagées (dont 03:17 et 12:57), corpus, manifeste, icônes, service worker,
fichiers communs, images d'aperçu, adresse inconnue, et une adresse de prévisualisation (<empreinte>.<projet>.pages.dev).
Chaque réponse doit renvoyer vers la connexion Cloudflare Access (ou être refusée) sans livrer le moindre texte du corpus.

--attente : contrôle de la page d'attente, avant l'envoi du contenu (seule l'adresse principale existe alors).
Code de sortie 0 seulement si tout est protégé : outils/deployer_essai.sh refuse d'envoyer le contenu sinon.
"""
import argparse, http.client, ssl, sys, urllib.parse

CHEMINS = ['/', '/index.html', '/?source=icone', '/m/0317-a1/', '/m/0317-a1', '/m/1257-a1/', '/m/0000-a1/', '/corpus/actuel.json',
           '/manifest.webmanifest', '/sw.js', '/icones/icone-512.png', '/icones/apple-touch-icon.png', '/commun/commun.css',
           '/commun/moteur.js', '/commun/carte.js', '/commun/media/b-fixe.jpg', '/apercus/s1/0317.jpg', '/robots.txt', '/adresse-inconnue']
INDICES = ['Quelqu’un voudrait', 'Quelqu\\u2019un', 'Synesthésie', '"creneaux"', '"definition"', 'data-heure']   # textes du corpus, jamais le nom de l'application

def demander(url):
    u = urllib.parse.urlsplit(url)
    c = http.client.HTTPSConnection(u.hostname, timeout=20, context=ssl.create_default_context())
    c.request('GET', (u.path or '/') + ('?' + u.query if u.query else ''), headers={'User-Agent': 'Mozilla/5.0 (controle-acces Chronographe LA)', 'Accept': '*/*'})
    r = c.getresponse(); corps = r.read(200_000).decode('utf-8', 'replace'); return r.status, r.getheader('Location') or '', corps

def protege(url):
    try: statut, lieu, corps = demander(url)
    except Exception as e: return None, f'injoignable ({e.__class__.__name__})'
    fuite = [i for i in INDICES if i in corps]
    vers_access = 'cloudflareaccess.com' in urllib.parse.urlsplit(lieu).netloc if lieu else False
    if statut in (301, 302, 303, 307, 308) and vers_access and not fuite: return True, f'{statut} → connexion Access'
    if statut in (401, 403) and not fuite: return True, f'{statut} refusé'
    if statut == 404 and not fuite and not lieu: return None, '404'
    return False, f'{statut} {lieu[:60]} ' + (f'— CONTENU VISIBLE : {", ".join(fuite)}' if fuite else '— pas de renvoi vers Access')

def main():
    a = argparse.ArgumentParser(); a.add_argument('url'); a.add_argument('--attente', action='store_true'); o = a.parse_args()
    base = o.url.rstrip('/'); hote = urllib.parse.urlsplit(base).hostname
    if not hote or not hote.endswith('.pages.dev'): sys.exit('ARRÊT : adresse attendue en https://<projet>.pages.dev')
    chemins = ['/', '/index.html', '/adresse-inconnue'] if o.attente else CHEMINS
    echecs = 0
    print(f'Contrôle sans connexion de {base} ({len(chemins)} adresses + prévisualisations)')
    for ch in chemins:
        ok, detail = protege(base + ch)
        if ok is None and o.attente and ch == '/adresse-inconnue': ok = True   # rien à cet endroit pendant l'attente
        echecs += ok is not True
        print(f'  {"✓" if ok else "✗"} {ch:28} {detail}')
    # prévisualisations : une empreinte inventée et l'alias de branche ; protégées ou inexistantes, jamais lisibles
    for sous in ['deadbeef', 'essai', 'main']:
        url = f'https://{sous}.{hote}/m/0317-a1/'; ok, detail = protege(url)
        if ok is None: ok, detail = True, detail + ' (aucune prévisualisation à cette adresse, rien de lisible)'
        echecs += ok is not True; print(f'  {"✓" if ok else "✗"} {sous}.{hote:18} {detail}')
    print('\nProtection complète : aucune adresse lisible sans connexion.' if not echecs else f'\n{echecs} adresse(s) NON protégée(s) : ne rien envoyer, ne pas diffuser l’adresse.')
    sys.exit(1 if echecs else 0)

if __name__ == '__main__': main()
