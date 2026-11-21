#!/usr/bin/env bash
# Le Chronographe LÀ — hébergement de la version d'essai « accès réservé » sur Cloudflare Pages.
# À lancer sur l'ordinateur de Souad (compte Cloudflare à son nom), seulement après son accord écrit.
#
#   ./outils/deployer_essai.sh attente   # 1 · crée le projet et n'envoie qu'une page d'attente, sans aucun texte
#   (configurer alors Cloudflare Access : voir ESSAIS-TELEPHONES.md, étape 4)
#   ./outils/deployer_essai.sh contenu   # 2 · contrôle la protection SANS connexion, puis seulement envoie la version d'essai
#   ./outils/deployer_essai.sh controle  # contrôle seul, à tout moment
#
# Garde-fous : jamais de domaine personnalisé (aucun réglage de editionsla.com ni de Squarespace), toujours la branche
# de production du projet d'essai (pas de prévisualisation supplémentaire), contenu refusé si une seule adresse est lisible
# sans connexion, dossier refusé s'il ne porte pas le bandeau « Version d'essai — accès réservé ».
set -euo pipefail
PROJET="${PROJET:-chronographe-la-essai}"
ICI="$(cd "$(dirname "$0")/.." && pwd)"
SITE="${SITE:-$ICI/../essai-acces-reserve}"
URL="https://$PROJET.pages.dev"
W="npx --yes wrangler@4"

confirmer() { read -r -p "$1 Taper OUI pour continuer : " r; [ "$r" = "OUI" ] || { echo "Arrêt, rien n'a été envoyé."; exit 1; }; }

case "${1:-}" in
  attente)
    confirmer "Créer le projet $PROJET sur VOTRE compte Cloudflare et y placer une page d'attente vide de tout texte ($URL) ?"
    $W whoami
    $W pages project create "$PROJET" --production-branch main || echo "(le projet existe peut-être déjà)"
    T="$(mktemp -d)"
    printf '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>Accès réservé</title></head><body><p>Accès réservé.</p></body></html>\n' > "$T/index.html"
    printf '/*\n  X-Robots-Tag: noindex, nofollow\n' > "$T/_headers"
    $W pages deploy "$T" --project-name "$PROJET" --branch main --commit-dirty=true
    echo; echo "Page d'attente en place : $URL"
    echo "Étape suivante : activer Cloudflare Access sur $PROJET.pages.dev et *.$PROJET.pages.dev (ESSAIS-TELEPHONES.md, étape 4), puis : $0 controle"
    ;;
  contenu)
    grep -q 'Version d’essai — accès réservé' "$SITE/index.html" || { echo "ARRÊT : $SITE n'est pas la construction « accès réservé » (python3 outils/construire_site.py --acces-reserve)"; exit 1; }
    [ ! -e "$SITE/CNAME" ] || { echo "ARRÊT : un fichier CNAME est présent dans $SITE"; exit 1; }
    echo "1 · Contrôle de la protection avant tout envoi"; python3 "$ICI/outils/controler_acces.py" "$URL" --attente || { echo "ARRÊT : la protection n'est pas active, rien n'est envoyé."; exit 1; }
    N=$(find "$SITE" -type f | wc -l | tr -d ' ')
    confirmer "Envoyer la version d'essai ($N fichiers) derrière l'accès réservé, sur $URL ?"
    $W pages deploy "$SITE" --project-name "$PROJET" --branch main --commit-dirty=true
    echo "2 · Contrôle de toutes les adresses après l'envoi"; sleep 20; python3 "$ICI/outils/controler_acces.py" "$URL" || {
      echo "ALERTE : une adresse est lisible sans connexion. Revenir à la page d'attente : $0 attente ; ne pas diffuser l'adresse."; exit 1; }
    ;;
  controle) python3 "$ICI/outils/controler_acces.py" "$URL" ;;
  *) sed -n '2,13p' "$0"; exit 1 ;;
esac
