# CV — Pierre-Luc Wagner

CV bilingue (EN / FR) généré à partir d'un fichier de données unique par langue.
Pas de dépendance à installer: Python 3.11+ (stdlib seulement) et Google Chrome.

## Utilisation

```bash
make            # construit HTML + PDF pour les deux langues dans dist/
make en         # anglais seulement
make fr         # français seulement
make html       # HTML seulement (rapide, pas de PDF)
make open       # construit et ouvre les PDF
make clean
```

## Publication

Le site est construit et déployé sur GitHub Pages par
`.github/workflows/pages.yml` à chaque push sur `main`. Le workflow refuse de
déployer si un CV dépasse deux pages ou si un fichier attendu manque.

`dist/index.html` est une page d'accueil générée automatiquement : choix de la
langue, lecture en ligne ou PDF.

> **Avant une première publication**: `scripts/prepare-public.sh`.
> Sépare le matériel privé et repart d'un historique neuf.

## Structure

| Chemin                 | Rôle |
|------------------------|------|
| `content/cv.en.toml`   | Contenu de la version anglaise |
| `content/cv.fr.toml`   | Contenu de la version française |
| `template/cv.css`      | Toute la mise en forme (écran + impression) |
| `build.py`             | Lit le TOML, rend le HTML, imprime le PDF via Chrome headless |
| `dist/`                | Sorties — `index.html`, `cv.en.*`, `cv.fr.*` |
| `.github/workflows/`   | Construction et déploiement sur GitHub Pages |

## Ajouter une expérience

Ajouter un bloc `[[experience]]` dans le fichier de la langue voulue:

```toml
[[experience]]
company  = "Nom de l'employeur"
role     = "Titre du poste"
location = "Montréal, QC"
start    = "2026"
end      = "présent"
context  = "Une ligne pour situer le contexte et l'échelle."
bullets  = [
  "Réalisation avec un **chiffre** dedans.",
  "Autre réalisation, avec du `terraform` en mono.",
]
tech = ["GCP", "Kubernetes", "Terraform"]
```

Les entrées consécutives qui partagent le même `company` sont regroupées
automatiquement sous un seul en-tête d'employeur (utile pour montrer une
progression de titres chez le même employeur).

Dans les `bullets` et les `context`, `**gras**` et `` `mono` `` fonctionnent.

## Longueur: tenir sur deux pages

`make` affiche le nombre de pages et avertit au-delà de deux. Si une langue
déborde, `base_pt` dans `[meta]` ajuste la taille de base du texte pour cette
langue seulement. Le français tourne à `9.7` parce qu'il est ~10 % plus long
que l'anglais à contenu égal. Ajuste ce nombre avant de couper du contenu.

## Format de papier

`letter` par défaut (Amérique du Nord). Pour l'Europe, change `paper` dans
la section `[meta]` du fichier de contenu ou lancer `make PAPER=a4`.
