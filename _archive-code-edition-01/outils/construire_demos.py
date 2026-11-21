"""
Le Chronographe LÀ — reconstruction des deux démonstrations privées (prototypes validés).

    python3 outils/construire_demos.py

  demos/compositions/   la sphère ouverte, composition verticale et horizontale, pastille, agrandissement (passe 4)
  demos/partage/        image à enregistrer, aperçu de lien, parcours du destinataire (passes 5 et 6)

Chaque démonstration est autonome (polices incluses, médias copiés depuis media/) et s'ouvre par un
simple serveur local : python3 -m http.server -d demos/partage 8000. Elles ne sont pas destinées à la mise en ligne.
"""
import base64, json, pathlib, re, shutil
R = pathlib.Path(__file__).resolve().parents[1]; S = R / 'sources'
b64 = lambda p: base64.b64encode(p.read_bytes()).decode()
POLICES = ('<style>@font-face{font-family:"EB Garamond";font-style:normal;font-weight:400 600;font-display:swap;'
           f'src:url(data:font/woff2;base64,{b64(S/"polices"/"ebg-roman.woff2")}) format("woff2")}}'
           '@font-face{font-family:"EB Garamond";font-style:italic;font-weight:400;font-display:swap;'
           f'src:url(data:font/woff2;base64,{b64(S/"polices"/"ebg-italic.woff2")}) format("woff2")}}</style>')
corpus = json.dumps(json.loads((S/'corpus'/'corpus.json').read_text()), ensure_ascii=False)
moteur = (S/'scripts'/'moteur.js').read_text()
for nom, gabarit in [('compositions', 'demo-compositions.html'), ('partage', 'demo-partage.html')]:
    t = (S/'gabarits'/gabarit).read_text().replace('<!--FONTS-->', POLICES).replace('/*CONSERVE*/', (S/'gabarits'/'pastille.css').read_text())
    commun = re.sub(r'@font-face\{[^}]*\}\n?', '', (S/'gabarits'/'commun.css').read_text())   # polices déjà incluses
    t = t.replace('{{PROPOS}}', json.loads((S/'config.json').read_text())['texte_propos'])
    t = t.replace('/*CORPUS*/', corpus).replace('/*MOTEUR*/', moteur).replace('/*COMMUN*/', commun)
    css = (S/'gabarits'/'commun.css').read_text(); t = t.replace('/*ACTIONS_CSS*/', css[css.index("/* Fenêtres d'action"):])
    # image de la sphère incluse dans la page : la carte peut être enregistrée même ouverte d'un double clic
    t = t.replace('/*SPHERE_DATA*/', 'data:image/jpeg;base64,' + b64(R/'media'/'b-fixe.jpg'))
    t = t.replace('/*CARTE*/', (S/'scripts'/'carte.js').read_text()).replace('/*ACTIONS*/', (S/'scripts'/'actions.js').read_text())
    d = R/'demos'/nom; (d/'media').mkdir(parents=True, exist_ok=True); (d/'index.html').write_text(t)
    for f in (R/'media').iterdir(): shutil.copy(f, d/'media'/f.name)
    print('demos/' + nom, f'{round(len(t)/1024)} Ko')
