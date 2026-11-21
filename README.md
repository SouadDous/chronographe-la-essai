# Le Chronographe LÀ

La nouvelle édition du Chronographe LÀ (Éditions LÀ), en ligne à https://chronographe.editionsla.com/

Ce dépôt ne contient que le site construit, produit par `outils/construire_site.py --definitif --enregistrer` dans le
dossier de production. Ne pas le modifier à la main : les adresses des instants partagés (`/m/…`) ne doivent jamais changer.
Indépendant de l’ancien Chronographe (dépôt `chronographe`).


## Édition 02 (21 novembre 2026)

Mise en ligne de l’édition 02 : 336 rencontres (mots, fragments, extraits de *Je me vois*), rotation sur 28 jours
(`commun/rotation_28_jours.js`, moteur d’Éditions LÀ, inclus tel quel en tête de `commun/moteur.js`), corpus public
`corpus/edition-02.json`. Partage : une page stable par rencontre, `/r/<identifiant>/`, sans heure.
Les 1 440 pages d’instants de l’édition 01 (`/m/…`) et `corpus/actuel.json` sont conservés à l’identique.
Sauvegarde de l’édition 01 : branche `sauvegarde-avant-e02` ; archive du site et du code : branche `archive-edition-01`.
