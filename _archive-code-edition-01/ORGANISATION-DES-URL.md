# Le Chronographe LÀ — organisation des adresses (proposition définitive)

État : **proposition, rien n’est activé.** Aucune modification du domaine, de Squarespace ou des dépôts existants n’a été faite.

## Les adresses

| Adresse | Rôle | Où |
|---|---|---|
| `editionsla.com/le-chronographe-la` | Page publique : l’adresse écrite sur l’image à enregistrer, dans les communications et la lettre. **Inchangée.** | Squarespace |
| `chronographe.editionsla.com` | L’objet lui-même : ouverture plein écran depuis la pastille, icône d’écran d’accueil. | Nouveau dépôt, GitHub Pages |
| `chronographe.editionsla.com/m/0317-a1` | Une minute partagée : son aperçu dans les messageries et sa page de réception. | Même dépôt |
| `chronographe.editionsla.com/apercus/s1/0317.jpg` | Image d’aperçu de cette minute (adresse technique, jamais montrée). | Même dépôt |
| Rubrique du livre *Je me vois* | L’ancienne œuvre, conservée. **Inchangée.** | Squarespace + `souaddous.github.io/chronographe` |

### Lire une adresse de minute

Le contenu change toutes les dix minutes, mais l’heure partagée est l’heure réelle, à la minute. Chaque minute a donc sa propre adresse, qui désigne le contenu de son créneau :

`/m/0317-a1` : **m** pour minute · **0317** l’heure envoyée · **a** le contenu du créneau 03:10 · **1** sa version.

`/m/0317-i1-v1` : un **contenu invité** sur ce créneau (**i1**), version **1**. Les identifiants invités ne peuvent pas se confondre avec ceux du corpus de base.

- Un contenu a dix adresses, une par minute de son créneau (`/m/0310-a1` à `/m/0319-a1`), chacune avec sa minute et la même rencontre.
- Correction d’un contenu → `/m/0317-a2`. L’adresse `/m/0317-a1` reste en ligne avec ses mots d’origine.
- Nouveau contenu pour le même créneau, lors d’une future édition du corpus → `/m/0317-b1`.
- Adresse inconnue ou incomplète (`/m/0317`) → la minute actuelle de la personne, jamais une page d’erreur.

## Pourquoi un sous-domaine d’editionsla.com

- Chaque minute partagée a besoin de sa propre page avec son titre et son image, lus par les messageries sans exécuter de code. Squarespace ne sait pas produire 1 440 pages de ce type ; un hébergement statique, si.
- Le nom du domaine reste celui des Éditions LÀ : c’est lui que les messageries affichent sous l’aperçu.
- L’adresse publique déjà diffusée, `editionsla.com/le-chronographe-la`, ne change pas.
- Coût nul : un enregistrement DNS chez le gestionnaire du domaine, l’hébergement gratuit de GitHub Pages, le HTTPS fourni par GitHub.

Écartés : des pages par minute sur Squarespace (impossible à cette échelle) ; une redirection depuis `editionsla.com/m/…` (une étape de plus, sans gain) ; un domaine séparé (coût, identité diluée) ; des adresses à paramètres `?minute=` (une page statique ne peut pas changer son aperçu selon le paramètre).

## Mise en place, le jour venu (rien de cela n’est fait)

1. Créer un nouveau dépôt pour le site (le dépôt actuel `chronographe` n’est pas touché). Choisir le compte : personnel ou organisation Éditions LÀ.
2. Y publier le contenu du dossier `publication/`, qui contient déjà le fichier `CNAME`.
3. Dans les réglages du dépôt, indiquer le domaine `chronographe.editionsla.com`. Vérifier le domaine dans les réglages GitHub, pour qu’aucun autre compte ne puisse le reprendre.
4. Chez le gestionnaire DNS du domaine : un enregistrement **CNAME**, hôte `chronographe`, valeur `<compte>.github.io` (sans nom de dépôt).
5. Une fois le DNS propagé (jusqu’à 24 h), cocher « Enforce HTTPS ».
6. Faire les tests d’aperçu dans les messageries, puis seulement relier la page publique et la pastille.

## Générer les pages et les aperçus, une fois le corpus prêt

Le corpus éditorial est fourni par Éditions LÀ (`sources/corpus/origine/chronographe_la_144.json`, jamais modifié) et converti par :

```sh
python outils/importer_corpus.py
```

L’outil écrit `sources/corpus/corpus.json` (le format du moteur, rubrique `creneaux`) et `sources/corpus/correspondance.csv` (la table des identifiants). Il compare ensuite chaque texte converti à l’original, champ par champ : à la moindre différence, il s’arrête sans rien écrire. Aucun texte n’est raccourci, reformulé, corrigé ni changé de casse.

| Fichier éditorial | Moteur | Remarque |
|---|---|---|
| `slot_start` (« 03:10 ») | clé du créneau | 144 créneaux, de 00:00 à 23:50 |
| `id` (`la01-0310-v1`) | `id_source` ; le moteur emploie `c0310-a` + `version` | adresses `/m/0310-a1` … `/m/0319-a1` |
| `type` | `type` | « mot » ou « fragment » |
| `term` | `mot` | deux formes (« Circonspect, circonspecte ») : retour à la ligne entre les formes |
| `grammar_and_domain` | `grammaire` | affichée telle quelle : « Nom féminin · Botanique » |
| `text` | `definition` (mot) ou `lignes` (fragment) | texte intégral |
| `author_credit` | `attribution` | absente quand elle vaut null ; distincte de la signature |
| `sources` (`title`, `url`, `purpose`) | `sources` (`titre`, `url`, `usage`) | ouvertes par le lien « Sources » |
| `publisher`, `editorial_status` | `editeur`, `statut` | conservés, jamais affichés ; un statut n’autorise jamais une mise en ligne |

Limites, fixées d’après le corpus réel : définition de 180 signes au plus (la plus longue en compte 178), fragment de 170 signes au plus (les fragments comptent de 52 à 106 signes). Un mot ou une forme plus large que la ligne du plus petit écran (6,8 em, environ 16 lettres) doit recevoir une césure conditionnelle ; aucun mot du corpus n’en a besoin.

Indications de présentation : `sources/corpus/presentation.json`, tenu à part du texte de référence. Aujourd’hui, une seule : la phrase témoin (`la01-0310-v1`) en deux blocs. L’import vérifie que la réunion des blocs redonne exactement le texte ; aucun autre fragment n’est découpé. L’indication s’applique au Chronographe, à la page reçue et à l’image à enregistrer.

Mise en page : quand le texte est long, seule la sphère cède de la place, jamais les caractères. Sur la page, elle peut descendre jusqu’à 62 % de sa taille prévue pour que le bouton reste visible ; sur le plus petit téléphone (320 × 568), un léger défilement complète. Sur l’image à enregistrer, la sphère varie entre 360 et 620 px pour que le texte intégral tienne dans le cadre. À l’affichage seulement, l’espace avant » : ; ! ? et après « devient insécable.

Puis :

```sh
python outils/verifier.py                          # tout contrôler (rien n’est publié)
python outils/construire_site.py                   # essai : construit publication/, ne promet rien
python outils/construire_site.py --enregistrer     # construction réellement mise en ligne, après validation
```

La construction :

- **refuse** un corpus incomplet ou fautif : créneau qui n’est pas un multiple de dix minutes, identifiant qui ne correspond pas au créneau, type inconnu, version manquante, champ absent, catégorie grammaticale inconnue, genre manquant pour un nom, source absente pour un mot, définition ou fragment trop long, mot trop long sans césure, caractère absent de la police (l’espace fine insécable est prise en charge) ;
- **refuse** toute inscription au registre (mise en ligne) tant que les statuts éditoriaux ne figurent pas dans `statuts_publiables` (`sources/config.json`), aujourd’hui vide ;
- **refuse** de modifier un contenu déjà publié (texte, attribution, nature, sources…) sans changer de version, ou de revenir à une version antérieure ;
- **refuse** de réécrire une page `/m/…` ou une image `/apercus/…` existante avec un autre contenu ;
- écrit dix pages par contenu et par version (une par minute du créneau) et une image d’aperçu par minute et par édition graphique : le contenu n’est pas dans l’image, il est dans le titre de l’aperçu ;
- ne génère aucun texte : il ne fait que mettre en page le corpus fourni ; rien n’est écrit au moment de la consultation ;
- inscrit au registre (`sources/corpus/registre.json`, seulement avec `--enregistrer`) chaque texte publié avec ses mots exacts, ce qui permet de reconstruire toutes les anciennes pages ;
- n’efface jamais rien dans le dossier de publication.

### Textes invités (structure prête, rien à gérer pour l’instant)

Le corpus des Éditions LÀ reste la base permanente. Un créneau peut recevoir, plus tard, un contenu invité (mot ou fragment, mêmes champs), avec son crédit et une période :

```json
"invites": {
  "03:10": [
    { "id": "c0310-i1", "version": 1, "type": "fragment", "lignes": [ "…" ],
      "auteur": { "nom": "…" }, "debut": "2027-03-01", "fin": "2027-03-31" }
  ]
}
```

- Du premier au dernier jour inclus, selon le calendrier de l’appareil du lecteur, le texte invité remplace la base dans l’affichage en direct, avec la ligne « Texte invité · Nom » (formulation provisoire). Le lendemain de la fin, la base reprend sa place seule, sans reconstruction du site.
- Une seule invitation à la fois par minute ; les chevauchements sont refusés. Prolonger ou avancer une période ne change pas l’adresse.
- Une minute invitée partagée garde son texte et son crédit pour toujours, même après l’échéance. Une minute de base partagée n’est jamais affectée par une invitation.
- Corriger le texte ou le crédit d’un invité publié exige une nouvelle version, comme pour la base.
- Les invitations à venir figurent dans le fichier public du corpus pour pouvoir commencer seules à leur date : un lecteur curieux pourrait les y lire avant. S’il faut un secret strict, on publiera l’invitation la veille de son début.
- Ni formulaire de contribution, ni gestion des candidatures, ni calendrier des auteurs : les invitations s’écrivent à la main dans le corpus.

### Volumes mesurés

- Pour 144 créneaux, soit 1 440 minutes : environ 6 Mo de pages et 109 Mo d’images d’aperçu (74 Ko chacune). Le rendu prend environ 3 minutes 30.
- Chaque correction ajoute dix pages d’environ 4 Ko et aucune image.
- La limite de 1 Go d’un site GitHub Pages laisse donc la place d’environ huit éditions graphiques complètes.

### Nouvelle animation de la sphère

1. `python outils/generer.py nouvelle.mp4` : visuels à comparer, rien d’autre n’est touché.
2. Une fois choisie : `python outils/generer.py nouvelle.mp4 --adopter`, puis passer `edition_graphique` à `s2` dans `sources/config.json`.
3. Les pages affichent la nouvelle sphère ; les images d’aperçu déjà partagées gardent l’ancienne, car les messageries les gardent en cache par adresse.

### L’image à enregistrer (1080 × 1350)

Elle présente l’heure envoyée et le contenu (le mot, sa nature et sa définition, ou le fragment et son attribution) : la préparer d’avance pour chaque minute et chaque version représenterait environ 700 Mo. La sphère seule s’ajuste au contenu, entre 420 et 620 px ; jamais les caractères. Elle sera donc dessinée par le navigateur au moment du partage, avec la même mise en page (gabarit `sources/gabarits/rendu.html`). Cette partie se construira avec l’objet définitif.
