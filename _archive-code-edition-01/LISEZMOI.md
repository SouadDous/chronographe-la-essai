# Le Chronographe LÀ — dossier de production

Version du 15 novembre 2026. Ce dossier contient tout ce qu’il faut pour régénérer les visuels, reconstruire les démonstrations et construire le futur site des minutes partagées, sans dépendre d’aucun autre fichier.

**Rien n’y est publié.** Aucun script ne se connecte au site Éditions LÀ, à Squarespace, à GitHub ou au domaine.

## Contenu

```
sources/                 ce qui fait foi (à conserver et à faire évoluer)
  animation/             l’animation B d’origine (Midjourney), jamais modifiée
  corpus/origine/        le corpus éditorial fourni par Éditions LÀ (144 rencontres), jamais modifié
  corpus/corpus.json     le même corpus au format du moteur (outils/importer_corpus.py), textes identiques
  corpus/correspondance.csv  la table des identifiants : fichier éditorial ↔ moteur ↔ adresses partagées
  corpus/presentation.json   indications d’affichage tenues à part (les deux blocs de la phrase témoin)
  corpus/registre.json   les textes publiés (vide : rien n’est en ligne)
  config.json            domaine, adresses, textes de l’aperçu, édition graphique
  gabarits/              page de minute, styles communs, outil de rendu, pastille, deux démonstrations
  scripts/               moteur de l’heure (moteur.js), le Chronographe (objet.js), la page reçue (recu.js),
                         la carte dessinée sur l’appareil (carte.js), les actions du lecteur (actions.js), sw.js
  polices/               EB Garamond : fichiers complets, sous-ensembles web, licence OFL
media/                   médias actuels de la sphère (provisoires, régénérables)
outils/                  les commandes ci-dessous
demos/                   les deux démonstrations privées, reconstruites et prêtes à ouvrir
controles/                le rapport des contrôles sur le corpus complet et des captures
ORGANISATION-DES-URL.md  la proposition définitive d’adresses, le format du corpus (mots et fragments) et la marche à suivre
ESSAIS-TELEPHONES.md     la version d’essai : page Squarespace non liée + copie GitHub Pages ; adresses, préalables,
                         essais dans la page / à l’adresse autonome, journal séparant machine et appareils réels
EMPREINTES.sha256        empreintes de tous les fichiers, pour vérifier une copie
```

## Installation (une fois)

Prérequis : Python 3.10 ou plus récent et ffmpeg (`brew install ffmpeg` sur Mac).

```sh
./installer.sh
. .env/bin/activate
python outils/verifier.py        # doit finir par « … vérifications réussies, 0 en échec »
```

## Les commandes

| Besoin | Commande | Ce qu’elle touche |
|---|---|---|
| Importer un nouveau corpus éditorial | `python outils/importer_corpus.py fichier.json` | `sources/corpus/corpus.json`, `correspondance.csv` |
| Tout vérifier (environ 6 minutes) | `python outils/verifier.py --rapport controles/rapport.md` | rien d’autre que le rapport |
| Nouvelle animation de la sphère | `python outils/generer.py animation.mp4` | `exports/<nom>/` seulement |
| L’adopter comme sphère courante | `python outils/generer.py animation.mp4 --adopter` | + `media/` |
| Reconstruire les démonstrations | `python outils/construire_demos.py` | `demos/` |
| Construire la version d’essai privée | `python outils/construire_site.py` | `publication/` (bandeau d’essai, liens vers la même adresse) |
| Construire la copie d’essai GitHub Pages (formule retenue) | `python outils/construire_site.py --chemin /chronographe-la-essai` | `../essai-github/` (sous-chemin, bandeau « adresse non diffusée », sans images d’aperçu ni CNAME) |
| Essai automatique page tierce + sous-chemin | `python outils/essayer_integration.py --rapport controles/rapport-integration.md` | le rapport et deux captures « squarespace-simulation » |
| Construire la copie à héberger derrière l’accès réservé (Cloudflare, non retenu) | `python outils/construire_site.py --acces-reserve` | `../essai-acces-reserve/` (bandeau « Version d’essai — accès réservé », sans domaine, non indexable) |
| Vérifier cette copie exacte (dont la connexion simulée) | `python outils/verifier.py --acces-reserve --rapport controles/rapport-controles.md` | le rapport |
| Captures de contrôle de la copie d’essai | `python outils/capturer.py` | `controles/captures/` + `PROVENANCE.txt` |
| (Cloudflare, non retenu) héberger la copie | `./outils/deployer_essai.sh attente` puis `contenu` | — |
| (Cloudflare, non retenu) contrôler la protection | `python outils/controler_acces.py …` | — |
| Construire le site définitif (après validation seulement) | `python outils/construire_site.py --definitif --enregistrer` | + `sources/corpus/registre.json` ; refusé tant qu’aucun statut n’autorise la publication |
| Refaire les sous-ensembles de police | `python outils/polices.py` | `sources/polices/*.woff2` |

Options de `generer.py` : `--image 30` choisit l’image fixe (numéro d’image dans la boucle), `--fondu 30` règle la longueur du fondu de boucle.

Le relevé `releve.json` indique la qualité du raccord : autour de 1 (fondu invisible) ; au-dessus de 2, le saut se voit.

## Ouvrir les démonstrations

```sh
python -m http.server -d demos/partage 8000        # puis http://localhost:8000
python -m http.server -d demos/compositions 8001   # puis http://localhost:8001
```

Les deux démonstrations s’ouvrent aussi d’un double clic sur leur `index.html`. Le menu « Relecture » parcourt les 144 créneaux (le créneau de la phrase témoin s’ouvre à 03:17) : c’est un outil de validation du prototype, pas une fonction publique.

## Points d’attention

- Les exports ne sont pas figés : la recherche chromatique sur la sphère B continue.
- La page d’accueil du site (`publication/index.html`) est le Chronographe lui-même, dans la composition horizontale validée (verticale sur téléphone).
- L’image à enregistrer est dessinée sur l’appareil du lecteur par `carte.js` ; les exports de l’atelier utilisent le même code.
- L’image à enregistrer sera dessinée au moment du partage (voir `ORGANISATION-DES-URL.md`).
- Le corpus ne se génère pas : il s’écrit. Les outils le vérifient, ils ne l’écrivent jamais.
- Le corpus de travail (72 mots, 72 fragments) est intégré tel quel. Ses statuts (« proposed_for_review », « previously_composed ») ne valent pas autorisation : la mise en ligne est bloquée tant que `statuts_publiables` est vide.
- Aucun texte n’est généré, ni à la construction ni à la consultation : les pages ne font qu’afficher le corpus fourni.
- Textes invités : la structure existe (rubrique `invites` du corpus, voir `ORGANISATION-DES-URL.md`) mais reste vide. Les vérifications en testent le fonctionnement avec des données d’essai qui ne sont jamais enregistrées.
- La police EB Garamond est sous licence SIL Open Font License (`sources/polices/OFL.txt`). Les sous-ensembles web en sont dérivés, sans nouveau dessin.

## Vérifier qu’une copie est complète

```sh
shasum -a 256 -c EMPREINTES.sha256
```
