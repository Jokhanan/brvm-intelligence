# BRVM Intelligence — dashboard auto-actualisé

Outil personnel d'aide à la décision pour investir à la BRVM.
Se met à jour **tout seul chaque jour** via GitHub Actions, servi gratuitement par GitHub Pages.

## Contenu du repo
- `brvm-intelligence.html` — le dashboard (screener, scoring, portefeuille, dividendes).
- `index.html` — copie servie par GitHub Pages (régénérée automatiquement).
- `update_brvm.py` — récupère les derniers cours et régénère le HTML. Aucune dépendance.
- `.github/workflows/update-brvm.yml` — relance le script chaque jour ouvré.

## Mise en route (≈ 5 min, une seule fois)
1. Créer un dépôt GitHub (privé ou public) et y déposer ces fichiers.
2. Lancer une première fois en local pour générer `index.html` :
   ```bash
   python3 update_brvm.py
   cp brvm-intelligence.html index.html
   git add -A && git commit -m "init" && git push
   ```
3. Dans le dépôt : **Settings → Pages → Source : Deploy from a branch → main / (root)**.
4. Au bout d'une minute, le dashboard est en ligne sur `https://<ton-pseudo>.github.io/<repo>/`.
5. Onglet **Actions** : vérifier que le workflow est activé. Il tournera chaque soir ;
   tu peux aussi le déclencher à la main (bouton « Run workflow »).

## Refaire à la main, sans GitHub
```bash
python3 update_brvm.py      # met à jour brvm-intelligence.html, puis ouvre-le
```

## Enrichir les fondamentaux
Les ratios (PER, P/B, rendement) ne sont calculés que pour les valeurs renseignées
dans le dictionnaire `REF` (en haut de `update_brvm.py`). Pour en ajouter, lis les
états financiers sur brvm.org et complète `shares`, `net`, `div`, `equity`, etc.

## Source des données
Dépôt public communautaire `Fredysessie/brvm-data-public` (cours BRVM, MàJ quotidienne, différé).
Outil personnel — ni conseil en investissement, ni données temps réel. 1 € = 655,957 FCFA.
