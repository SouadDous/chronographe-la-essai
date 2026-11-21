"""
Le Chronographe LÀ — sous-ensembles web de la police EB Garamond (licence SIL OFL, voir sources/polices/OFL.txt).

    python3 outils/polices.py

Produit sources/polices/ebg-roman.woff2 et ebg-italic.woff2 à partir des fichiers complets de
sources/polices/originales/. Le jeu de caractères couvre le français complet (dont Œ œ Ÿ « » ’ … –)
et les signes courants. EB Garamond ne contient pas l'espace fine insécable (U+202F), indispensable
en typographie française : on la fait pointer vers le dessin de l'espace fine (U+2009), sans rien
dessiner de nouveau. La vérification du corpus (pages_minutes.py) refuse tout caractère absent.
"""
import pathlib, subprocess, sys, tempfile
from fontTools.ttLib import TTFont

R = pathlib.Path(__file__).resolve().parents[1]
P = R / 'sources' / 'polices'
PLAGES = 'U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+0178,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2190-2193,U+2212'

def construire(src, dst):
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t) / 'f.ttf'
        f = TTFont(src)
        for table in f['cmap'].tables:
            if table.isUnicode() and 0x2009 in table.cmap:
                table.cmap.setdefault(0x202F, table.cmap[0x2009])   # espace fine insécable → dessin de l'espace fine
        f.save(tmp)
        subprocess.run([sys.executable, '-m', 'fontTools.subset', str(tmp), f'--unicodes={PLAGES}',
                        '--layout-features=kern,liga,lnum,tnum,onum,pnum,case,frac', '--flavor=woff2',
                        f'--output-file={dst}'], check=True)
    print(dst.name, f'{round(dst.stat().st_size/1024)} Ko', len(TTFont(dst).getBestCmap()), 'caractères')

def caracteres():
    """Caractères disponibles dans les deux sous-ensembles (pour la vérification du corpus)."""
    r = TTFont(P / 'ebg-roman.woff2').getBestCmap(); i = TTFont(P / 'ebg-italic.woff2').getBestCmap()
    return set(r) & set(i)

if __name__ == '__main__':
    construire(P / 'originales' / 'EBGaramond.ttf', P / 'ebg-roman.woff2')
    construire(P / 'originales' / 'EBGaramond-Italic.ttf', P / 'ebg-italic.woff2')
