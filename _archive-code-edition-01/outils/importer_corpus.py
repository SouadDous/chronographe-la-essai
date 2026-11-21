"""
Le Chronographe LÀ — import du corpus éditorial dans le format du moteur.

    python3 outils/importer_corpus.py [sources/corpus/origine/chronographe_la_144.json]

Lit le fichier fourni par Éditions LÀ (jamais modifié) et écrit :
  sources/corpus/corpus.json            le corpus au format du moteur (rubrique « creneaux ») ;
  sources/corpus/correspondance.csv     la table des identifiants : fichier éditorial ↔ moteur ↔ adresses.
Il lit aussi sources/corpus/presentation.json : des indications d'affichage tenues à part (par exemple les deux
blocs de la phrase témoin). Elles s'ajoutent au contenu sous « presentation » sans toucher au texte, et l'import
vérifie que leur réunion redonne exactement le texte de référence.

Aucun texte n'est modifié : ni raccourci, ni reformulé, ni corrigé, ni changé de casse. Après conversion,
l'outil relit le résultat et compare chaque champ à l'original, octet par octet ; à la moindre différence,
il s'arrête sans rien écrire.

Correspondance des champs :
  slot_start            → clé du créneau (« 03:10 »)
  id  (la01-0310-v1)    → id_source ; le moteur emploie c0310-a + version 1 (adresses /m/0310-a1 … /m/0319-a1)
  version               → version
  type                  → type (« mot » ou « fragment »)
  term                  → mot
  grammar_and_domain    → grammaire (affichée telle quelle : « Nom féminin · Botanique »)
  text                  → definition (mot) ou lignes[0] (fragment)
  author_credit         → attribution (absente quand elle vaut null)
  publisher             → editeur
  sources[title,url,purpose] → sources[titre,url,usage]
  editorial_status      → statut (information de relecture ; n'autorise jamais une mise en ligne)
  slot_end_exclusive, start_minute_of_day, duration_minutes : recalculés et vérifiés, non recopiés
"""
import csv, json, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else R / 'sources/corpus/origine/chronographe_la_144.json'

def convertir(o, presentation=None):
    presentation = {k: v for k, v in (presentation or {}).items() if not k.startswith('_')}
    creneaux, lignes_csv, erreurs = {}, [], []
    attendus = [f'{h:02d}:{m:02d}' for h in range(24) for m in range(0, 60, 10)]
    for e in o['entries']:
        k = e['slot_start']; h, m = map(int, k.split(':'))
        if e['start_minute_of_day'] != h * 60 + m or e['duration_minutes'] != 10:
            erreurs.append(f'{e["id"]} : horaires incohérents')
        fin = h * 60 + m + 10
        if e['slot_end_exclusive'] != f'{fin // 60 % 24:02d}:{fin % 60:02d}': erreurs.append(f'{e["id"]} : fin de créneau incohérente')
        if k in creneaux: erreurs.append(f'{k} : créneau en double')
        c = {'id': 'c' + k.replace(':', '') + '-a', 'version': e['version'], 'id_source': e['id'], 'type': e['type']}
        if e['type'] == 'mot':
            c.update(mot=e['term'], grammaire=e['grammar_and_domain'], definition=e['text'])
        elif e['type'] == 'fragment':
            c['lignes'] = [e['text']]
        else: erreurs.append(f'{e["id"]} : type inconnu {e["type"]!r}')
        if e.get('author_credit'): c['attribution'] = e['author_credit'] if isinstance(e['author_credit'], dict) else {'auteur': e['author_credit']}
        if e.get('sources'): c['sources'] = [{'titre': s['title'], 'url': s['url'], **({'usage': s['purpose']} if s.get('purpose') else {})} for s in e['sources']]
        p = presentation.pop(e['id'], None)
        if p:
            par = p.get('paragraphes')
            if e['type'] != 'fragment' or not isinstance(par, list) or not par or ' '.join(par) != e['text']:
                erreurs.append(f'{e["id"]} : indication de présentation qui ne redonne pas exactement le texte de référence')
            else: c['presentation'] = {'paragraphes': par}
        c['editeur'] = e['publisher']; c['statut'] = e['editorial_status']
        creneaux[k] = c
        lignes_csv.append([k, e['id'], c['id'], c['version'], e['type'], e['term'] or '', f'/m/{k.replace(":", "")}-a{c["version"]} … /m/{k[:4].replace(":", "")}9-a{c["version"]}', e['editorial_status']])
    if presentation: erreurs.append(f'indications de présentation sans contenu correspondant : {sorted(presentation)}')
    if sorted(creneaux) != attendus: erreurs.append(f'créneaux manquants : {sorted(set(attendus) - set(creneaux))}')
    corpus = {
        'edition': o['edition_id'], 'titre': o['title'], 'promesse_source': o['tagline'], 'langue': o['language'],
        'note': 'Corpus de travail fourni par Éditions LÀ (144 rencontres : 72 mots, 72 fragments), converti sans modifier aucun texte. '
                'Les statuts éditoriaux ne valent pas autorisation de mise en ligne.',
        'etat_publication': o['publication_state'], 'provenance': o['provenance'], 'notes_integration': o['integration_notes'],
        'rythme': 'Le contenu change toutes les dix minutes (créneaux 00, 10, 20, 30, 40, 50) ; l’heure affichée reste l’heure réelle de l’appareil.',
        'regle': 'meme-contenu-au-meme-creneau', 'archives': {}, 'creneaux': creneaux, 'invites': {}}
    return corpus, lignes_csv, erreurs

def verifier_identite(o, corpus):
    """Chaque texte du fichier éditorial se retrouve à l'identique dans le corpus converti."""
    diff = []
    for e in o['entries']:
        c = corpus['creneaux'][e['slot_start']]
        texte = c['definition'] if e['type'] == 'mot' else c['lignes'][0]
        paires = [('text', e['text'], texte)]
        if e['type'] == 'mot': paires += [('term', e['term'], c['mot']), ('grammar_and_domain', e['grammar_and_domain'], c['grammaire'])]
        paires += [('sources', [(s['title'], s['url'], s.get('purpose')) for s in e['sources']], [(s['titre'], s['url'], s.get('usage')) for s in c.get('sources', [])]),
                   ('editorial_status', e['editorial_status'], c['statut']), ('publisher', e['publisher'], c['editeur']), ('version', e['version'], c['version'])]
        for nom, a, b in paires:
            if a != b: diff.append(f'{e["id"]} · {nom} : {a!r} ≠ {b!r}')
    return diff

if __name__ == '__main__':
    o = json.loads(SRC.read_text())
    pres_p = R / 'sources/corpus/presentation.json'
    corpus, lignes, erreurs = convertir(o, json.loads(pres_p.read_text()) if pres_p.exists() else None)
    texte = json.dumps(corpus, ensure_ascii=False, indent=2) + '\n'
    diff = verifier_identite(o, json.loads(texte))
    if erreurs or diff: print('ARRÊT, rien n’est écrit :\n  ' + '\n  '.join(erreurs + diff)); sys.exit(1)
    (R / 'sources/corpus/corpus.json').write_text(texte)
    with open(R / 'sources/corpus/correspondance.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['creneau', 'id_fichier_editorial', 'id_moteur', 'version', 'type', 'mot', 'adresses_partagees', 'statut_editorial'])
        w.writerows(lignes)
    n = len(o['entries'])
    print(f'{n} contenus convertis ({sum(1 for e in o["entries"] if e["type"]=="mot")} mots, {sum(1 for e in o["entries"] if e["type"]=="fragment")} fragments) ; '
          f'{n} textes identiques à l’original, champ par champ.')
