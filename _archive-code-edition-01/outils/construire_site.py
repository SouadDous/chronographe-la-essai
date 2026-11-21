"""
Le Chronographe LÀ — construction du site statique (pages de minute et aperçus de lien).

    python3 outils/construire_site.py [--sortie publication] [--media media] [--enregistrer]

Lit :   sources/config.json, sources/corpus/corpus.json, sources/corpus/registre.json,
        sources/gabarits/*, sources/scripts/*, sources/polices/*.woff2, et les médias de la sphère.
Écrit : le dossier de publication (par défaut publication/), qui deviendra le dépôt du site.

Règles de conservation (elles ne se désactivent pas) :
  - Le contenu change toutes les dix minutes ; l'heure partagée est l'heure réelle, à la minute.
  - Un instant partagé a une adresse définitive : /m/<HHMM>-<lettre><version>, par exemple /m/0317-a1
    (minute 03:17, contenu a de son créneau 03:10, version 1) ; dix adresses par contenu et par version.
  - Tout contenu enregistré au registre reste publié pour toujours, avec ses mots d'origine.
  - Modifier un contenu enregistré sans changer son numéro de version est refusé : on crée la version suivante.
  - Le dossier de publication est cumulatif : rien n'y est jamais effacé ; une page /m/… ou une image
    /apercus/… existante n'est jamais réécrite avec un autre contenu.
  - --enregistrer inscrit les textes actuels au registre. À n'utiliser que pour la construction
    réellement mise en ligne (après validation). Sans ce drapeau, la construction est un essai.
"""
import argparse, datetime, functools, hashlib, html, http.server, json, pathlib, re, shutil, sys, threading, asyncio, io

R = pathlib.Path(__file__).resolve().parents[1]
S = R / 'sources'
sys.path.insert(0, str(R / 'outils'))

class Erreur(Exception): pass

def empreinte(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
def lire_json(p, defaut=None): return json.loads(p.read_text()) if p.exists() else defaut

# ---------------------------------------------------------------- vérification du corpus
# Le contenu change toutes les dix minutes : 144 créneaux par jour (HH:00, HH:10 … HH:50).
# Deux sortes de contenus : un mot (avec sa définition) ou un fragment littéraire.
# Identifiants distincts :
#   contenu de base (corpus Éditions LÀ, permanent)    c0310-a   (créneau 03:10, contenu a)
#   contenu invité (remplace la base entre deux dates)  c0310-i1
# Chaque minute du créneau a sa propre adresse partagée, car l'heure envoyée est l'heure réelle :
#   /m/0317-a1  = minute 03:17, contenu a de son créneau, version 1 ;  /m/0317-i1-v1 pour un invité.
CRENEAU = r'([01]\d|2[0-3]):[0-5]0'
LIMITES = {'em': 6.8, 'signes': 180, 'fragment': 170}
POLICE = None   # (cmap, hmtx, unités) de la police romaine, chargée par construire()
DATE = r'\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])'

CHAMPS = ['type', 'mot', 'grammaire', 'nature', 'genre', 'indication', 'definition', 'lignes', 'presentation', 'attribution', 'sources']
META = ['id_source', 'editeur', 'statut']   # conservés et transmis, mais hors de l'empreinte : ils ne s'affichent pas
CATEGORIES = ('Nom', 'Verbe', 'Adjectif', 'Adverbe', 'Interjection', 'Préposition', 'Conjonction', 'Pronom', 'Déterminant', 'Locution', 'Article', 'Onomatopée')
NATURES = ('nom', 'verbe', 'adjectif', 'adverbe', 'interjection', 'préposition', 'conjonction', 'pronom', 'déterminant', 'locution', 'article', 'onomatopée')
GENRES = ('masculin', 'féminin', 'masculin et féminin')

def notice(t):
    """Les champs publiés d'un contenu (mot ou fragment)."""
    return {k: t[k] for k in CHAMPS if t.get(k) not in (None, '', [], {})}

def contenu(t):
    """Ce qui fait l'identité d'un contenu publié : tous ses champs, sources comprises, et le crédit d'un invité."""
    return json.dumps({**notice(t), **({'auteur': t['auteur']} if t.get('invite') else {})}, ensure_ascii=False, sort_keys=True)

def sans_cesure(s): return s.replace('\u00ad', '')

def largeur_em(mot, police):
    """Largeur du plus long segment insécable : chaque forme (« Circonspect, circonspecte »), chaque mot
    d'une locution (« Se déliter ») et chaque segment de césure conditionnelle doit tenir sur une ligne."""
    cm, hm, upm = police
    segs = [s for forme in re.split(r',\s*', mot) for s in (forme + ',').replace(' ', '\u00ad').split('\u00ad')]
    return max(sum(hm[cm[ord(c)]][0] for c in seg if ord(c) in cm) / upm for seg in segs if seg)

def minutes_du_creneau(creneau):
    h, m = creneau.split(':'); return [f'{h}:{int(m) + i:02d}' for i in range(10)]

def slug(t, minute=None):
    """Adresse d'une minute partagée (par défaut la première minute du créneau)."""
    h = (minute or t['heure']).replace(':', '')
    return f'{h}-i{t["numero"]}-v{t["version"]}' if t.get('invite') else f'{h}-{t["lettre"]}{t["version"]}'

def verifier_sources(ou, src, obligatoire, erreurs):
    if src is None and not obligatoire: return []
    if not isinstance(src, list) or (obligatoire and not src) or not all(isinstance(s, dict) and isinstance(s.get('titre'), str) and s['titre'].strip() for s in src):
        erreurs.append(f'{ou} : ' + ('au moins une source attendue' if obligatoire else 'sources mal formées') + ' ({"titre": …, "url": …})'); return []
    for s in src:
        if s.get('url') is not None and not re.fullmatch(r'https://\S+', str(s['url'])): erreurs.append(f'{ou} : adresse de source invalide ({s.get("url")}) — https:// attendu')
    return [s['titre'] for s in src]

def verifier_texte(heure, e, invite, caracteres, erreurs, avertissements):
    ou = f'{"contenu invité" if invite else "créneau"} {heure}'
    hhmm = heure.replace(':', '')
    motif = rf'c{hhmm}-i([1-9]\d*)' if invite else rf'c{hhmm}-([a-z])'
    m = re.fullmatch(motif, str(e.get('id', '')))
    if not m:
        erreurs.append(f'{ou} : identifiant « {e.get("id")} » invalide (attendu ' + (f'c{hhmm}-i1, c{hhmm}-i2…)' if invite else f'c{hhmm}-a, c{hhmm}-b…)')); return None
    ou = f'{ou} ({e["id"]})'
    v = e.get('version')
    if not isinstance(v, int) or isinstance(v, bool) or v < 1: erreurs.append(f'{ou} : version invalide ({v!r})'); return None
    t = {'heure': heure, 'id': e['id'], 'version': v}
    typ = e.get('type')
    if typ == 'mot':
        for k in ('mot', 'definition'):
            if not isinstance(e.get(k), str) or not e[k].strip(): erreurs.append(f'{ou} : champ « {k} » absent ou vide'); return None
        mot, definition = e['mot'], e['definition']
        if 'grammaire' in e:
            gram = e['grammaire']
            if not isinstance(gram, str) or not gram.strip(): erreurs.append(f'{ou} : indication grammaticale vide'); return None
            cat = gram.split(' · ')[0]
            if not cat.startswith(CATEGORIES): erreurs.append(f'{ou} : catégorie grammaticale « {cat} » inconnue')
            if cat.startswith('Nom') and not any(g in cat for g in ('masculin', 'féminin')): erreurs.append(f'{ou} : genre attendu pour un nom (« Nom féminin »…)')
            if not cat.startswith('Nom') and any(g in cat for g in ('masculin', 'féminin')): erreurs.append(f'{ou} : le genre ne s’indique que pour un nom')
            a_gram = [gram]
        else:
            if not isinstance(e.get('nature'), str) or not e['nature'].strip(): erreurs.append(f'{ou} : indication grammaticale absente (« grammaire »)'); return None
            nature = e['nature']
            if not nature.startswith(NATURES): erreurs.append(f'{ou} : nature « {nature} » inconnue (en toutes lettres : {", ".join(NATURES)}…)')
            genre = e.get('genre')
            if nature.startswith('nom'):
                if genre not in GENRES: erreurs.append(f'{ou} : genre attendu pour un nom ({", ".join(GENRES)})')
            elif genre is not None: erreurs.append(f'{ou} : le genre ne s’indique que pour un nom')
            ind = e.get('indication')
            if ind is not None and (not isinstance(ind, str) or not ind.strip()): erreurs.append(f'{ou} : indication vide (retirez le champ)')
            a_gram = [nature, ind or '']
        titres = verifier_sources(ou, e.get('sources'), True, erreurs)
        if '­' in definition + ''.join(a_gram): erreurs.append(f'{ou} : la césure conditionnelle n’est admise que dans le mot')
        if len(definition) > LIMITES['signes']: erreurs.append(f'{ou} : définition de {len(definition)} signes (maximum {LIMITES["signes"]}, pour rester lisible sur l’image à enregistrer)')
        a_verifier = [mot, definition] + a_gram + titres
    elif typ == 'fragment':
        lignes = e.get('lignes')
        if not isinstance(lignes, list) or not lignes or not all(isinstance(l, str) and l.strip() for l in lignes):
            erreurs.append(f'{ou} : lignes du fragment absentes ou vides'); return None
        n = sum(len(l) for l in lignes)
        if n > LIMITES['fragment']: erreurs.append(f'{ou} : fragment de {n} signes (maximum {LIMITES["fragment"]}, pour rester lisible sur le plus petit écran et sur l’image à enregistrer)')
        pres = e.get('presentation')
        if pres is not None and (not isinstance(pres, dict) or ' '.join(pres.get('paragraphes') or []) != ' '.join(lignes)):
            erreurs.append(f'{ou} : indication de présentation qui ne redonne pas exactement le texte')
        att = e.get('attribution')
        if att is not None and (not isinstance(att, dict) or not any(isinstance(att.get(k), str) and att[k].strip() for k in ('auteur', 'oeuvre'))):
            erreurs.append(f'{ou} : attribution mal formée ({{"auteur": …, "oeuvre": …}})')
        titres = verifier_sources(ou, e.get('sources'), False, erreurs)
        if any('­' in l for l in lignes): avertissements.append(f'{ou} : césure conditionnelle dans le fragment')
        a_verifier = list(lignes) + [str(v) for v in (att or {}).values()] + titres
    else:
        erreurs.append(f'{ou} : type « {typ} » inconnu (« mot » ou « fragment »)'); return None
    for k, val in e.items():
        if isinstance(val, str) and (val != val.strip() or '  ' in val): avertissements.append(f'{ou} : espaces superflues dans « {k} »')
    t.update({k: e[k] for k in CHAMPS + META if k in e})
    if invite:
        nom = (e.get('auteur') or {}).get('nom') if isinstance(e.get('auteur'), dict) else None
        if not isinstance(nom, str) or not nom.strip(): erreurs.append(f'{ou} : crédit auteur absent ("auteur": {{"nom": "…"}})'); return None
        d, f = e.get('debut'), e.get('fin')
        if not (isinstance(d, str) and re.fullmatch(DATE, d) and isinstance(f, str) and re.fullmatch(DATE, f)):
            erreurs.append(f'{ou} : dates de début et de fin attendues au format AAAA-MM-JJ'); return None
        if d > f: erreurs.append(f'{ou} : la fin ({f}) précède le début ({d})'); return None
        t.update({'invite': True, 'numero': int(m.group(1)), 'auteur': nom, 'debut': d, 'fin': f}); a_verifier.append(nom)
    else:
        t['lettre'] = m.group(1)
    absents = sorted({c for l in a_verifier for c in l if ord(c) not in caracteres})
    if absents: erreurs.append(f'{ou} : caractères absents de la police : ' + ' '.join(f'{c!r} (U+{ord(c):04X})' for c in absents))
    if typ == 'mot' and POLICE and not absents:
        l = largeur_em(e['mot'], POLICE)
        if l > LIMITES['em']:
            erreurs.append(f'{ou} : « {sans_cesure(e["mot"])} » mesure {l:.2f} em, plus que la ligne du plus petit écran ({LIMITES["em"]} em). '
                           'Les caractères ne sont pas réduits : indiquez une césure conditionnelle (U+00AD) dans le mot.')
    return t

def verifier_corpus(corpus, registre, caracteres):
    erreurs, avertissements, textes = [], [], {}
    def ajouter(t):
        cle = f'{t["id"]}@{t["version"]}'
        if cle in textes: erreurs.append(f'{cle} : identifiant utilisé deux fois')
        textes[cle] = t
    if 'minutes' in corpus: erreurs.append('le corpus utilise l’ancienne rubrique « minutes » : les contenus se rangent désormais par créneau de dix minutes (« creneaux »)')
    for heure, e in sorted(corpus.get('creneaux', {}).items()):
        if not re.fullmatch(CRENEAU, heure): erreurs.append(f'créneau {heure} : clé invalide (HH:00, HH:10 … HH:50 attendu)'); continue
        t = verifier_texte(heure, e, False, caracteres, erreurs, avertissements)
        if t: ajouter(t)
    for heure, liste in sorted((corpus.get('invites') or {}).items()):
        if not re.fullmatch(CRENEAU, heure): erreurs.append(f'contenu invité {heure} : clé invalide (HH:00, HH:10 … HH:50 attendu)'); continue
        if not isinstance(liste, list): erreurs.append(f'contenu invité {heure} : une liste est attendue'); continue
        periodes = []
        for e in liste:
            t = verifier_texte(heure, e, True, caracteres, erreurs, avertissements)
            if not t: continue
            ajouter(t)
            for autre in periodes:   # une seule invitation à la fois sur un créneau
                if t['debut'] <= autre['fin'] and autre['debut'] <= t['fin']:
                    erreurs.append(f'{heure} : les périodes de {autre["id"]} et {t["id"]} se chevauchent')
            periodes.append(t)
    # conservation : ce qui est enregistré ne change jamais
    for cle, t in textes.items():
        r = registre['textes'].get(cle)
        if r and r['empreinte'] != empreinte(contenu(t)):
            erreurs.append(f'{cle} : ce contenu est déjà publié ; pour le corriger, gardez l’identifiant et passez à la version {t["version"]+1}')
        plus_hautes = [x['version'] for x in registre['textes'].values() if x['id'] == t['id'] and x['version'] > t['version']]
        if plus_hautes: erreurs.append(f'{cle} : la version {max(plus_hautes)} est déjà publiée ; une version ne peut pas reculer')
    return textes, erreurs, avertissements

# ---------------------------------------------------------------- écriture prudente
# Adresses de la racine du site (« /commun/… », « /m/… », « / ») réécrites sous un sous-chemin, pour une copie
# servie à <compte>.github.io/<projet>/. Seuls les fichiers texte sont touchés ; les adresses complètes (https://…) restent.
PREFIXABLE = re.compile(r'(?<=["\'(=])/(?=(?:commun|m|corpus|icones|apercus)/|manifest\.webmanifest|sw\.js|\?source|index\.html|["\')])')
def prefixeur(chemin):
    if not chemin: return None
    chemin = '/' + chemin.strip('/')
    def f(nom, b):
        if not nom.endswith(('.html', '.js', '.css', '.json', '.webmanifest')): return b
        return PREFIXABLE.sub(chemin + '/', b.decode()).encode()
    return f

class Ecrivain:
    def __init__(self, racine, transformer=None): self.racine = racine; self.transformer = transformer; self.journal = {'cree': [], 'identique': [], 'remplace': []}
    def ecrire(self, chemin, contenu, immuable=False):
        p = self.racine / chemin; b = contenu if isinstance(contenu, bytes) else contenu.encode()
        if self.transformer: b = self.transformer(chemin, b)
        if p.exists():
            if p.read_bytes() == b: self.journal['identique'].append(chemin); return
            if immuable: raise Erreur(f'{chemin} existe déjà avec un autre contenu : une adresse publiée ne change jamais')
            self.journal['remplace'].append(chemin)
        else: self.journal['cree'].append(chemin)
        p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b)

def notice_html(t):
    """Même rendu que ChronoLA.contenuHTML (moteur.js), écrit dans la page pour être lisible sans script."""
    # même règle d'affichage que moteur.js : espaces insécables autour de « » : ; ! ? (le corpus reste inchangé)
    e = lambda s: re.sub(r' ([»:;!?])', '\u00a0\\1', s).replace('« ', '«\u00a0').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    credit = f'<p class="credit">Texte invité · {e(t["auteur"])}</p>' if t.get('invite') else ''
    voir = '<p class="voir"><button type="button" class="sources" data-sources>Sources</button></p>' if t.get('sources') else ''
    if t['type'] == 'fragment':
        a = t.get('attribution') or {}
        att = ''
        if a.get('auteur') or a.get('oeuvre'):
            att = ('<p class="attribution">' + (e(a['auteur']) if a.get('auteur') else '') + (', ' if a.get('auteur') and a.get('oeuvre') else '')
                   + (f'<cite>{e(a["oeuvre"])}</cite>' if a.get('oeuvre') else '') + '</p>')
        blocs = (t.get('presentation') or {}).get('paragraphes') or t['lignes']
        return '<div class="contenu fragment">' + ''.join(f'<p class="texte">{e(l)}</p>' for l in blocs) + att + credit + voir + '</div>'
    nat = t['grammaire'] if 'grammaire' in t else t['nature'] + (' ' + t['genre'] if t.get('genre') else '') + (' · ' + t['indication'] if t.get('indication') else '')
    formes = re.split(r',\s*', t['mot'])
    mot = e(t['mot']) if len(formes) < 2 else ' '.join(f'<span class="forme">{e(f)}{"," if i < len(formes) - 1 else ""}</span>' for i, f in enumerate(formes))
    return ('<div class="contenu mot-def">' f'<p class="mot" lang="fr">{mot}</p>'
            f'<p class="nature">{e(nat)}</p>'
            f'<p class="definition">{e(t["definition"])}</p>' + credit + voir + '</div>')

def titre_apercu(cfg, t, minute):
    if t['type'] == 'fragment':
        a = t.get('attribution') or {}
        titre = cfg['titre_fragment'].format(heure=minute, texte=' '.join(t['lignes'])) + (f' — {a["auteur"]}' if a.get('auteur') else '')
    else:
        titre = cfg['titre_mot'].format(heure=minute, mot=sans_cesure(t['mot']), definition=t['definition'])
    return titre + (cfg['suffixe_invite'].format(auteur=t['auteur']) if t.get('invite') else '')

def remplir(modele, valeurs):
    for k, v in valeurs.items(): modele = modele.replace('{{' + k + '}}', v)
    reste = re.findall(r'\{\{[A-Z_]+\}\}', modele)
    if reste: raise Erreur('gabarit : champs non remplis ' + ', '.join(reste))
    return modele


# ---------------------------------------------------------------- icônes (dérivées de l'image fixe de la sphère)
def icones(image):
    """Icône retenue (17 novembre) : celle du premier Chronographe, « LÀ » blanc sur fond noir, reprise telle quelle
    (sources/icones/la-noir-premier-chronographe-512.png, copiée du dépôt SouadDous/chronographe sans le modifier).
    Remplace l'icône « LÀ » noir sur la sphère du 16 novembre. Icône Apple 180 px, 192 et 512 px, et 512 px
    « masquable » : les lettres sont réduites dans la zone sûre centrale de 80 % sur le même noir."""
    from PIL import Image
    src = Image.open(S / 'icones' / 'la-noir-premier-chronographe-512.png').convert('RGB'); sortie = {}
    def png(im):
        buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True); return buf.getvalue()
    def faire(taille):
        return png(src.resize((taille, taille), Image.LANCZOS))
    def masquable(taille):
        fond = Image.new('RGB', (taille, taille), src.getpixel((4, 4)))
        t = int(taille * 0.78); fond.paste(src.resize((t, t), Image.LANCZOS), ((taille - t) // 2, (taille - t) // 2))
        return png(fond)
    sortie['apple-touch-icon.png'] = faire(180)
    sortie['icone-192.png'] = faire(192)
    sortie['icone-512.png'] = faire(512)
    sortie['icone-masquable-512.png'] = masquable(512)
    return sortie

# ---------------------------------------------------------------- rendu des aperçus
async def rendre_apercus(racine, heures, edition, ecr):
    from playwright.async_api import async_playwright
    from PIL import Image
    shutil.copy(S / 'gabarits' / 'rendu.html', racine / '_rendu.html')
    class Silencieux(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Silencieux, directory=str(racine))
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        async with async_playwright() as p:
            b = await __import__('navigateur').lancer(p)
            pg = await b.new_page(viewport={'width': 1200, 'height': 630})
            for heure in heures:
                await pg.goto(f'http://127.0.0.1:{port}/_rendu.html#og/{heure}')
                await pg.wait_for_function('document.body.dataset.pret==="1"')
                png = await pg.locator('#r').screenshot()
                im = Image.open(io.BytesIO(png)).convert('RGB'); q = 90
                while True:
                    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=q, optimize=True, progressive=True)
                    if buf.tell() < 300 * 1024 or q <= 60: break
                    q -= 5
                ecr.ecrire(f'apercus/{edition}/{heure.replace(":", "")}.jpg', buf.getvalue(), immuable=True)
            await b.close()
    finally:
        srv.shutdown(); (racine / '_rendu.html').unlink(missing_ok=True)

# ---------------------------------------------------------------- construction
def construire(sortie, media, enregistrer=False, corpus_p=None, registre_p=None, essai=True, acces_reserve=False, chemin=''):
    import polices
    cfg = lire_json(S / 'config.json'); corpus = lire_json(corpus_p or S / 'corpus' / 'corpus.json')
    reg_p = registre_p or S / 'corpus' / 'registre.json'; registre = lire_json(reg_p, {'textes': {}})
    global POLICE
    from fontTools.ttLib import TTFont
    f = TTFont(S / 'polices' / 'ebg-roman.woff2'); POLICE = (f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm)
    LIMITES.update(em=cfg.get('mot_largeur_max_em', 6.8), signes=cfg.get('definition_signes_max', 180), fragment=cfg.get('fragment_signes_max', 170))
    textes, erreurs, avert = verifier_corpus(corpus, registre, polices.caracteres())
    for a in avert: print('  attention :', a)
    if erreurs: raise Erreur('corpus refusé :\n  - ' + '\n  - '.join(erreurs))
    if enregistrer:   # un statut de relecture n'est jamais une autorisation de mise en ligne
        permis = set(cfg.get('statuts_publiables') or [])
        bloques = sorted({t.get('statut', '(sans statut)') for t in textes.values() if t.get('statut') not in permis})
        if bloques: raise Erreur('enregistrement refusé : statut(s) éditorial(aux) non autorisé(s) pour la mise en ligne : ' + ', '.join(bloques) +
                                 ' (voir « statuts_publiables » dans sources/config.json)')

    if chemin and (acces_reserve or not essai): raise Erreur('--chemin sert seulement à la copie d’essai GitHub Pages')
    sortie.mkdir(parents=True, exist_ok=True); ecr = Ecrivain(sortie, prefixeur(chemin))
    D = 'https://' + cfg['domaine']; ed = cfg['edition_graphique']; esc = lambda t: html.escape(t, quote=True)

    # 1 · fichiers communs (remplaçables : ils servent toutes les pages)
    commun = {'commun/commun.css': (S/'gabarits'/'commun.css').read_bytes(), 'commun/objet.css': (S/'gabarits'/'objet.css').read_bytes()}
    for f in ['moteur.js', 'recu.js', 'carte.js', 'actions.js', 'objet.js']: commun['commun/' + f] = (S/'scripts'/f).read_bytes()
    for f in ['ebg-roman.woff2', 'ebg-italic.woff2']: commun['commun/polices/' + f] = (S/'polices'/f).read_bytes()
    for f in ['b-624.mp4', 'b-208.mp4', 'b-lent-624.mp4', 'b-lent-208.mp4', 'b-fixe.jpg', 'b-fixe-208.jpg']:
        commun['commun/media/' + f] = (media / f).read_bytes()
    for k, v in commun.items(): ecr.ecrire(k, v)
    # Invitations : celles qui ne sont pas échues (marge d'un jour pour les fuseaux horaires des lecteurs).
    # Les invitations à venir y figurent déjà, pour commencer seules à leur date : elles sont lisibles dans ce fichier.
    veille = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    invites = {h: [e for e in l if e['fin'] >= veille] for h, l in (corpus.get('invites') or {}).items()}
    # le fichier public ne contient que ce qui s'affiche : ni statut éditorial, ni identifiant interne, ni éditeur
    public = lambda e: {k: v for k, v in e.items() if k not in META}
    actuel = {'edition': corpus.get('edition', ''), 'regle': corpus.get('regle', ''),
              'creneaux': {h: public(e) for h, e in corpus.get('creneaux', {}).items()},
              'invites': {h: [public(e) for e in l] for h, l in invites.items() if l}}
    ecr.ecrire('corpus/actuel.json', json.dumps(actuel, ensure_ascii=False, indent=1))
    if chemin:          # copie d'essai GitHub Pages : surtout pas de CNAME (il tenterait de prendre un domaine)
        ecr.ecrire('.nojekyll', '')
    elif acces_reserve:   # copie d'essai hébergée derrière Cloudflare Access : aucun domaine, rien d'indexable
        ecr.ecrire('_headers', '/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: same-origin\n/sw.js\n  Cache-Control: no-cache\n')
        ecr.ecrire('robots.txt', 'User-agent: *\nDisallow: /\n')
    else:
        ecr.ecrire('CNAME', cfg['domaine'] + '\n'); ecr.ecrire('.nojekyll', '')
        ecr.ecrire('robots.txt', 'User-agent: *\nAllow: /\n')   # ne rien bloquer : les messageries lisent robots.txt
    ecr.ecrire('404.html', '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>' + esc(cfg['nom']) +
               '</title><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=/"></head>'
               '<body><script>location.replace("/")</script><p><a href="/">' + esc(cfg['nom']) + '</a></p></body></html>\n')

    modele = (S / 'gabarits' / 'minute.html').read_text()
    # Les pages appellent les fichiers communs à adresse fixe, sans empreinte : une page publiée ne change donc
    # jamais quand on améliore la mise en page (sinon la règle « une adresse publiée ne change jamais » bloquerait
    # toute correction). Les pages déjà partagées profitent ainsi des corrections d'affichage, jamais de texte.
    emp = {}
    base = {'PROMESSE': esc(cfg['promesse']), 'INVITATION': esc(cfg['invitation']), 'NOM': esc(cfg['nom']), 'EDITEUR': esc(cfg['editeur']), 'SITE_EDITIONS': esc(cfg['site_editions']),
            'DESCRIPTION': esc(cfg['description']), 'TEXTE_PROPOS': esc(cfg['texte_propos']),
            'ROBOTS': '' if cfg.get('indexation_des_minutes') else '<meta name="robots" content="noindex">\n'}

    # 2 · le Chronographe (page d'accueil), le manifeste, les icônes et le service worker
    actions = {'promesse': cfg['promesse'], 'invitation': cfg['invitation'], 'adresse': cfg['adresse_ecrite'], 'sphere': '/commun/media/b-fixe.jpg'}
    bandeau = cfg['bandeau_essai_github'] if chemin else cfg['bandeau_acces_reserve'] if acces_reserve else cfg['bandeau_essai_court']
    if essai: actions['essai'] = cfg['note_essai_github'] if chemin else cfg['note_acces_reserve'] if acces_reserve else cfg['bandeau_essai']   # liens vers la version d'essai (même origine)
    else: actions['base'] = D                                    # version définitive : liens sur le domaine prévu
    base['ACTIONS_JSON'] = json.dumps(actions, ensure_ascii=False).replace('</', '<\\/')
    base['NOM_COURT'] = esc(cfg['nom_court'])
    base['BANDEAU_ESSAI'] = f'<p class="essai">{esc(bandeau)}</p>\n' if essai else ''
    objet = remplir((S / 'gabarits' / 'chronographe.html').read_text(), {**base, 'PAGE_PUBLIQUE': esc(cfg['page_publique']),
                    'ROBOTS_OBJET': '<meta name="robots" content="noindex">\n' if essai else '', 'CANONIQUE': esc(cfg['page_publique']) if essai else D + '/'})
    ecr.ecrire('index.html', objet)
    manifeste = {'id': '/', 'name': cfg['nom'], 'short_name': cfg['nom_court'], 'lang': 'fr', 'dir': 'ltr',
                 'description': cfg['description'], 'start_url': '/?source=icone', 'scope': '/', 'display': 'standalone',
                 'background_color': '#F6F3ED', 'theme_color': '#F6F3ED',
                 'icons': [{'src': '/icones/icone-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
                           {'src': '/icones/icone-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
                           {'src': '/icones/icone-masquable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}
    ecr.ecrire('manifest.webmanifest', json.dumps(manifeste, ensure_ascii=False, indent=1))
    for nom, png in icones(media / 'b-fixe.jpg').items(): ecr.ecrire('icones/' + nom, png)
    version = empreinte(b''.join(commun[k] for k in sorted(commun)) + json.dumps(actuel, sort_keys=True).encode())[:12]
    ecr.ecrire('sw.js', (S / 'scripts' / 'sw.js').read_text().replace('{{VERSION}}', version))

    # 3 · une page par minute partagée : chaque contenu (registre + corpus actuel), pour chacune des dix minutes de son créneau
    a_publier = {k: {**v, 'edition_graphique': v['edition_graphique']} for k, v in registre['textes'].items()}
    for k, t in textes.items(): a_publier.setdefault(k, {**t, 'edition_graphique': ed})
    pages = 0
    for cle, t in sorted(a_publier.items()):
        n = notice(t)
        donnees = {'creneau': t['heure'], 'id': t['id'], 'version': t['version'], **n}
        if t.get('invite'): donnees.update({'invite': True, 'auteur': {'nom': t['auteur']}})
        corps = notice_html(t)
        for minute in minutes_du_creneau(t['heure']):
            s = slug(t, minute); url = f'{D}/m/{s}'; img = f'{D}/apercus/{t["edition_graphique"]}/{minute.replace(":", "")}.jpg'
            page = remplir(modele, {**base, **emp, 'TITRE': esc(titre_apercu(cfg, t, minute)), 'URL': url,
                'IMAGE': img, 'IMAGE_ALT': esc(f'Un instant partagé, {minute}. {cfg["nom"]}, {cfg["editeur"]}.'),
                'ETAT': 'Un instant pour vous', 'HEURE': minute, 'NOTICE_HTML': corps,
                'MINUTE_JSON': json.dumps({'heure': minute, **donnees}, ensure_ascii=False).replace('</', '<\\/')})
            ecr.ecrire(f'm/{s}/index.html', page, immuable=True); pages += 1

    # 4 · images d'aperçu manquantes (une par minute et par édition graphique ; le contenu est dans le titre)
    voulues = {(t['edition_graphique'], m) for t in a_publier.values() for m in minutes_du_creneau(t['heure'])}
    manquantes = sorted((e, m) for e, m in voulues if not (sortie / 'apercus' / e / (m.replace(':', '') + '.jpg')).exists())
    autres = {e for e, _ in manquantes if e != ed}
    if autres: raise Erreur(f'images d’aperçu manquantes pour une ancienne édition graphique ({", ".join(autres)}) : '
                            'restaurez le dossier de publication depuis son dépôt, elles ne se recalculent pas')
    if chemin: manquantes = []   # copie d'essai GitHub : pas d'images d'aperçu (elles servent aux messageries, phase 2 décidée à part)
    if manquantes: asyncio.run(rendre_apercus(sortie, [h for _, h in manquantes], ed, ecr))

    # 5 · registre
    if enregistrer:
        jour = datetime.date.today().isoformat()
        for cle, t in textes.items():
            if cle not in registre['textes']:
                registre['textes'][cle] = {**t, 'empreinte': empreinte(contenu(t)), 'adresses': f'/m/{slug(t)} … /m/{slug(t, minutes_du_creneau(t["heure"])[-1])}',
                                           'edition_graphique': ed, 'enregistre': jour}
        reg_p.write_text(json.dumps(registre, ensure_ascii=False, indent=1) + '\n')

    poids = sum(f.stat().st_size for f in sortie.rglob('*') if f.is_file())
    rapport = {'contenus': len(a_publier), 'pages_de_minute': pages, 'dont_nouvelles': sum(1 for c in ecr.journal['cree'] if c.startswith('m/')),
               'apercus_rendus': len(manquantes), 'fichiers_crees': len(ecr.journal['cree']), 'fichiers_remplaces': ecr.journal['remplace'],
               'poids_total_Mo': round(poids / 1e6, 1), 'registre_mis_a_jour': enregistrer}
    print(json.dumps(rapport, ensure_ascii=False, indent=1)); return rapport

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--sortie', default=str(R / 'publication')); a.add_argument('--media', default=str(R / 'media'))
    a.add_argument('--enregistrer', action='store_true')
    a.add_argument('--definitif', action='store_true', help='liens sur le domaine prévu, sans bandeau d’essai (après validation seulement)')
    a.add_argument('--acces-reserve', action='store_true', help='copie d’essai à héberger derrière Cloudflare Access (« Version d’essai — accès réservé »)')
    a.add_argument('--chemin', default='', help='copie d’essai GitHub Pages servie sous ce sous-chemin, ex. /chronographe-la-essai')
    o = a.parse_args()
    if o.chemin and (o.definitif or o.enregistrer or o.acces_reserve): print('ARRÊT : --chemin est une construction d’essai seule'); sys.exit(1)
    if o.chemin and o.sortie == str(R / 'publication'): o.sortie = str(R.parent / 'essai-github')
    if o.acces_reserve and (o.definitif or o.enregistrer): print('ARRÊT : --acces-reserve est une construction d’essai, sans --definitif ni --enregistrer'); sys.exit(1)
    if o.acces_reserve and o.sortie == str(R / 'publication'): o.sortie = str(R.parent / 'essai-acces-reserve')
    try: construire(pathlib.Path(o.sortie), pathlib.Path(o.media), o.enregistrer, essai=not o.definitif, acces_reserve=o.acces_reserve, chemin=o.chemin)
    except Erreur as e: print('ARRÊT :', e); sys.exit(1)
