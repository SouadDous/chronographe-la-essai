# Le Chronographe LÀ — mise en ligne et essais

**En ligne depuis le 16 novembre 2026 : https://chronographe.editionsla.com/**

- **Hébergement.** GitHub Pages, dépôt `SouadDous/chronographe-la-essai` (à renommer `chronographe-la` si souhaité ; le domaine n’en dépend pas). Le dépôt contient la version définitive, construite par `outils/construire_site.py --definitif --enregistrer` dans `../site-definitif/`.
- **Domaine.** Chez Gandi, enregistrement `chronographe CNAME 300 souaddous.github.io.`, ajouté le 16/11/2026. Les autres enregistrements sont inchangés.
- **Ancienne adresse d’essai.** `souaddous.github.io/chronographe-la-essai/…` renvoie vers la nouvelle adresse : les instants partagés pendant les essais restent valides.
- **Site Éditions LÀ (Squarespace)**
  - Page `/le-chronographe-la` : le bloc Code affiche désormais le nouveau Chronographe, dans un cadre de 720 px de haut. La ligne « Une phrase de présence, chaque minute. » est remplacée par la promesse. La mise en page mobile a été ajustée.
  - Pied de page global : un bloc Code contient la pastille (icône « LÀ » sur la sphère, en bas à gauche, au-dessus du bouton des cookies) avec le lien vers le Chronographe.
  - CSS personnalisé : trois règles à la fin, pour que la pastille reste visible au-dessus du contenu et sans fondu.
- **Corpus.** Les statuts actuels sont déclarés publiables (décision du 16/11/2026, `sources/config.json`). Registre : `sources/corpus/registre.json`, 144 textes.
- **Ancien Chronographe.** `souaddous.github.io/chronographe` et son dépôt restent intacts. Il n’est plus affiché sur la page du site.
- **Reste à faire, côté Souad :**
  - cocher « Enforce HTTPS » dans les réglages Pages du dépôt, dès que GitHub le propose ;
  - décider de la phrase « œuvre générative » sur la page du site.

---

# Le Chronographe LÀ — version d’essai : page Squarespace + copie GitHub Pages

**État au 16 novembre 2026 : copie d’essai en ligne** à `https://souaddous.github.io/chronographe-la-essai/` (dépôt `SouadDous/chronographe-la-essai`, GitHub Pages activé par Souad). Page Squarespace : non créée (forfait Essentiel : pas de cadre possible ; une page non liée avec un simple lien reste possible si besoin). Le site public, la page actuelle
`/le-chronographe-la`, l’ancien Chronographe (`souaddous.github.io/chronographe` et son dépôt), le domaine et ses réglages
restent tels quels. Aucune pastille n’est ajoutée au site.

La formule Cloudflare (accès par e-mail) n’est pas retenue. Ses outils restent dans le dossier pour mémoire, mais ne servent pas.

## La formule

1. **Une page Squarespace « non liée »**, masquée des résultats de recherche, avec un mot de passe de page si vous le
   souhaitez. Elle affiche le Chronographe dans un **bloc Code** (un cadre `iframe`).
2. **Un nouveau projet GitHub Pages, indépendant**, dans votre compte : `souaddous/chronographe-la-essai`. Il héberge les
   fichiers du Chronographe à son **adresse autonome**. C’est cette adresse que l’on partage, que l’on ajoute à l’écran
   d’accueil et qui ouvre les minutes partagées. Le dépôt de l’ancien Chronographe n’est pas touché.

### Adresses qui deviendraient accessibles

| Adresse | Accès | Contenu |
|---|---|---|
| `https://www.editionsla.com/<adresse-de-la-page>` (au choix, par ex. `/chronographe-essai`) | Toute personne qui a l’adresse ; avec mot de passe si vous en mettez un. Absente du menu et des résultats de recherche | La page qui présente le Chronographe |
| `https://souaddous.github.io/chronographe-la-essai/` | **Publique** pour toute personne qui a ou devine l’adresse. Non annoncée, non indexée (`noindex`) | Le Chronographe autonome |
| `https://souaddous.github.io/chronographe-la-essai/m/0000-a1` … `/m/2359-a1` | Publique, comme ci-dessus | Les 1 440 minutes partagées |
| `https://souaddous.github.io/chronographe-la-essai/corpus/actuel.json` | Publique, comme ci-dessus | Les 144 rencontres (texte complet, sans statut ni identifiant interne) |
| `https://github.com/souaddous/chronographe-la-essai` | **Dépôt public** : l’offre GitHub gratuite n’héberge de pages que depuis un dépôt public | Les mêmes fichiers (le site construit uniquement : ni outils, ni corpus source, ni registre) |

**Important.**
- Le mot de passe de la page Squarespace ne protège que cette page. Il ne protège ni l’adresse GitHub, ni les minutes,
  ni le fichier du corpus, ni le dépôt.
- Une copie publique GitHub Pages n’est pas une version privée. C’est une adresse non diffusée.
- Le bandeau affiché sur chaque page est « Version d’essai — adresse non diffusée ».

### Ce que l’ancien Chronographe partage avec la copie d’essai

Les deux sont servis depuis la même origine, `souaddous.github.io`. La copie d’essai a été réglée pour ne jamais toucher aux données de l’ancien :
- le service worker ne couvre que `/chronographe-la-essai/` ;
- il n’efface que ses propres caches ;
- le manifeste a sa propre identité, son propre démarrage et sa propre portée.

L’essai automatique le vérifie, avec un ancien Chronographe factice installé sur la même origine.

## Préalables (aucun compte nouveau, aucune dépense)

1. **Squarespace :** l’affichage d’un cadre dans un bloc Code demande un forfait Core (anciennement Business) ou supérieur. Merci de confirmer votre forfait.
2. **GitHub :** créer un dépôt **public vide** nommé `chronographe-la-essai` dans votre compte `souaddous`.
3. **Envoi des fichiers (1 465 fichiers, 19 Mo).** Le dépôt par le navigateur est limité à 100 fichiers par envoi. Deux possibilités :
   - vous reliez GitHub à Claude (Réglages › Connecteurs) et m’autorisez l’écriture sur ce seul dépôt : j’y envoie le site construit ;
   - vous l’envoyez vous-même avec GitHub Desktop, depuis le dossier `essai-github` que je vous fournis.
4. **Activer Pages :** dans le dépôt, Settings › Pages › « Deploy from a branch », branche `main`, dossier `/ (root)`.
   Ne rien saisir dans « Custom domain ».

## Le bloc Code à placer dans la page Squarespace

```html
<iframe src="https://souaddous.github.io/chronographe-la-essai/"
        title="Le Chronographe LÀ — version d’essai"
        allow="web-share; clipboard-write"
        style="display:block;width:100%;height:100svh;min-height:600px;border:0"
        loading="eager"></iframe>
```

Réglages de la page :
- dans « Non lié » ;
- SEO › « Masquer cette page des résultats de recherche » ;
- mot de passe facultatif.

## Où faire chaque essai

### A · Dans la page Squarespace

Ce qui se vérifie ici : le Chronographe tel qu’il apparaîtrait dans le site.

| Essai | Résultat attendu (vérifié en simulation) |
|---|---|
| Sphère animée, heure, lecture | Le Chronographe s’affiche dans la page, avec la sphère |
| Changement de rencontre aux minutes 00, 10, 20… | La rencontre change dans la page |
| Ergonomie dans la page | Sur ordinateur, la composition tient dans le cadre. Sur téléphone, on fait défiler la page du site jusqu’au cadre |
| Commandes « Partager cet instant », « Copier le lien », « Enregistrer l’image » | Elles fonctionnent ; le lien partagé est l’**adresse autonome** de la minute (GitHub), jamais la page Squarespace |
| « Envoyer le lien » (feuille de partage) | Autorisé par `allow="web-share"`. Le comportement exact varie selon le navigateur : à observer |
| Lien « ← Éditions LÀ » | Ouvre le site à la place de la page, pas dans le cadre |
| « Ajouter à mon écran d’accueil » | Pas depuis la page : l’icône ouvrirait la page Squarespace. L’aide l’explique et propose « Ouvrir le Chronographe » à son adresse autonome |

### B · En ouvrant directement l’adresse autonome

| Essai | Pourquoi ici |
|---|---|
| Ajout à l’écran d’accueil, icône, nom sous l’icône | L’icône doit ouvrir le Chronographe, pas la page Squarespace |
| Réouverture par l’icône, le jour même puis le lendemain | Elle passe par le service worker de l’adresse autonome |
| Ouverture d’un lien reçu (minute et texte exacts, puis « Ouvrir le Chronographe ») | Les liens partagés mènent à l’adresse autonome |
| Partage à cheval sur un créneau (xx:x9 et 50 s) | Le lien doit porter la minute du clic |
| Enregistrement de la carte dans Photos ou dans la Galerie | Le comportement natif du téléphone est plus fiable hors cadre |

Les aperçus dans les messageries (phase 2) seront décidés à part : l’image et l’adresse des aperçus ne sont pas prêtes, et la copie d’essai ne contient pas d’images d’aperçu.

## Journal

### 1 · Contrôles automatisés (machine)

Ces contrôles tournent dans Chrome sous Linux, avec des téléphones simulés par leur taille d’écran et leur identité de navigateur. Ils ne remplacent aucun essai réel.
- `python3 outils/verifier.py` : corpus, rythme, affichage, cartes, partage, parcours complet ;
- `python3 outils/essayer_integration.py` : page tierce et cadre, sous-chemin, cohabitation avec l’ancien Chronographe ;
- `python3 outils/capturer.py` : captures de la copie exacte (`controles/captures/PROVENANCE.txt`).

### 2 · Essais dans la page Squarespace (vrais appareils)

| Date | Testeur | Téléphone ou ordinateur (modèle) | Système (version) | Navigateur (version) | Essai | Résultat réellement observé | Capture |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | *Aucun essai réel effectué à ce jour* | — |

### 3 · Essais à l’adresse autonome (vrais appareils)

| Date | Testeur | Téléphone ou ordinateur (modèle) | Système (version) | Navigateur (version) | Essai | Résultat réellement observé | Capture |
|---|---|---|---|---|---|---|---|
| 16/11/2026 | Souad | deux téléphones (modèles à préciser) | à préciser | à préciser | Partage d’une minute de l’un à l’autre, ouverture du lien reçu | « Tout m’a l’air très bien » | — |
| 16/11/2026 | Souad | à préciser | à préciser | à préciser | Lecture de 18:55 à 18:57 : même rencontre (« Assonance ») | Conforme au rythme de dix minutes (créneau 18:50) | — |

On n’inscrit que ce qui a été réellement observé sur l’appareil, jamais un résultat attendu.
