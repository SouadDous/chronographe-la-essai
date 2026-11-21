# Essai automatique : page Squarespace + copie GitHub Pages (simulation locale)

Contrôles automatisés dans Chrome ; ils ne remplacent pas les essais sur de vrais téléphones.

- ✓ le Chronographe s’ouvre sous le sous-chemin, sans aucune ressource manquante
- ✓ « Partager cet instant » donne l’adresse autonome de la minute
- ✓ la page reçue 03:17 s’ouvre, phrase témoin en deux blocs
- ✓ « Ouvrir le Chronographe » reste dans le projet
- ✓ le service worker ne couvre que le projet
- ✓ manifeste : identité, démarrage et portée propres au projet (distincts de l’ancien Chronographe)
- ✓ Chrome juge le Chronographe installable à son adresse autonome
- ✓ les données de l’ancien Chronographe (même origine) sont intactes
- ✓ réouverture « par l’icône » hors connexion : le Chronographe s’affiche
- ✓ téléphone : le Chronographe s’affiche dans la page, avec la sphère
- ✓ téléphone : les liens vers le site Éditions LÀ s’ouvrent à la place de la page, pas dans le cadre
- ✓ téléphone : le changement de rencontre a lieu à 13:00 dans la page
- ✓ téléphone : la composition tient dans le cadre (390 × 844)
- ✓ téléphone : « Partager » dans la page donne l’adresse autonome de la minute (13:00), pas la page du site
- ✓ téléphone : « Copier le lien » fonctionne dans la page
- ✓ téléphone : « Enregistrer l’image » fonctionne dans la page (téléchargement)
- ✓ téléphone : « Ajouter à mon écran d’accueil » dans la page renvoie vers l’adresse autonome (l’ajout depuis la page installerait la page du site)
- ✓ ordinateur : le Chronographe s’affiche dans la page, avec la sphère
- ✓ ordinateur : les liens vers le site Éditions LÀ s’ouvrent à la place de la page, pas dans le cadre
- ✓ ordinateur : le changement de rencontre a lieu à 13:00 dans la page
- ✓ ordinateur : la composition tient dans le cadre (1440 × 900)
- ✓ ordinateur : « Partager » dans la page donne l’adresse autonome de la minute (13:00), pas la page du site
- ✓ ordinateur : « Copier le lien » fonctionne dans la page
- ✓ ordinateur : « Enregistrer l’image » fonctionne dans la page (téléchargement)
- ✓ ordinateur : « Ajouter à mon écran d’accueil » dans la page renvoie vers l’adresse autonome (l’ajout depuis la page installerait la page du site)
- ✓ une minute reçue (03:17) s’affiche aussi dans la page, en deux blocs

26 réussies, 0 en échec.
