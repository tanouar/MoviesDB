# Guide de configuration des credentials — Pipeline Colab

Ce guide explique comment configurer les credentials Neo4j AuraDB pour exécuter
le notebook `notebooks/Pipeline_Colab.ipynb` dans les deux contextes supportés :
**Google Colab** (interactif) et **GitHub Actions** (automatisé via papermill).

---

## Credentials requis

| Clé              | Description                                           | Exemple                                      |
|------------------|-------------------------------------------------------|----------------------------------------------|
| `NEO4J_URI`      | URI de connexion AuraDB (toujours `neo4j+s://...`)   | `neo4j+s://xxxxxxxx.databases.neo4j.io`      |
| `NEO4J_USERNAME` | Nom d'utilisateur (par défaut `neo4j`)               | `neo4j`                                      |
| `NEO4J_PASSWORD` | Mot de passe généré à la création de l'instance      | `Abc123...`                                  |
| `NEO4J_DATABASE` | Nom de la base (par défaut `neo4j`)                  | `neo4j`                                      |

Ces informations sont disponibles dans le fichier `.env` ou dans la console
[Neo4j Aura](https://console.neo4j.io) après création de l'instance.

---

## Option A — Google Colab (exécution interactive)

Les Colab Secrets permettent de stocker des credentials sans les écrire dans le
notebook. Ils sont chiffrés et liés à votre compte Google.

### Étapes

1. Ouvrir le notebook `Pipeline_Colab.ipynb` dans Google Colab.

2. Dans la barre latérale gauche, cliquer sur l'icône **🔑 Secrets**
   (ou aller dans **Outils → Secrets**).

3. Ajouter chacun des secrets suivants avec le bouton **+ Ajouter un secret** :

   | Nom              | Valeur                                          |
   |------------------|-------------------------------------------------|
   | `NEO4J_URI`      | `neo4j+s://xxxxxxxx.databases.neo4j.io`         |
   | `NEO4J_USERNAME` | `neo4j`                                         |
   | `NEO4J_PASSWORD` | votre mot de passe AuraDB                       |
   | `NEO4J_DATABASE` | `neo4j`                                         |

4. Activer l'accès au secret pour ce notebook avec le **toggle** en face de
   chaque secret.

5. Exécuter le notebook normalement (**Exécution → Tout exécuter**).

> **Important** : Les secrets Colab ne sont **jamais** visibles dans le code
> ni dans les outputs du notebook. Ils ne sont pas inclus si vous partagez le
> notebook.

---

## Option B — GitHub Actions (exécution automatisée via papermill)

Le workflow GitHub Actions lance le notebook via
[papermill](https://papermill.readthedocs.io) et injecte les credentials
depuis les **Secrets GitHub** sous forme de variables d'environnement.

### 1. Configurer les secrets du dépôt

1. Aller dans **Settings → Secrets and variables → Actions** du dépôt GitHub.

2. Cliquer sur **New repository secret** et ajouter :

   | Secret           | Valeur                                          |
   |------------------|-------------------------------------------------|
   | `NEO4J_URI`      | `neo4j+s://xxxxxxxx.databases.neo4j.io`         |
   | `NEO4J_USERNAME` | `neo4j`                                         |
   | `NEO4J_PASSWORD` | votre mot de passe AuraDB                       |
   | `NEO4J_DATABASE` | `neo4j`                                         |

### 2. Workflow GitHub Actions correspondant

Créer ou mettre à jour `.github/workflows/pipeline.yml` :

```yaml
name: Pipeline — MCU DuckDB → AuraDB

on:
  schedule:
    - cron: "0 10 * * 1"  # Tous les lundis à 10h UTC
  workflow_dispatch:

jobs:
  run-pipeline:
    name: Exécuter Pipeline_Colab via papermill
    runs-on: ubuntu-latest

    steps:
      - name: Checkout du dépôt
        uses: actions/checkout@v4

      - name: Configurer Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Installer les dépendances
        run: |
          pip install papermill jupyter ipykernel \
            duckdb neo4j pandas requests lxml python-dotenv

      - name: Exécuter le notebook
        env:
          NEO4J_URI:      ${{ secrets.NEO4J_URI }}
          NEO4J_USERNAME: ${{ secrets.NEO4J_USERNAME }}
          NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
          NEO4J_DATABASE: ${{ secrets.NEO4J_DATABASE }}
        run: |
          papermill notebooks/Pipeline_Colab.ipynb /dev/null \
            --kernel python3 \
            --report-mode
```

> **Note** : Le notebook lit les credentials depuis `os.environ`, qui hérite
> automatiquement des variables `env:` définies dans le step GitHub Actions.
> Aucune modification du code du notebook n'est nécessaire.

---

## Vérifier la connexion à AuraDB

Pour tester manuellement que vos credentials sont valides avant d'exécuter
la pipeline complète :

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j+s://xxxxxxxx.databases.neo4j.io",
    auth=("neo4j", "votre-mot-de-passe")
)
with driver.session() as session:
    result = session.run("RETURN 1 AS ok").single()
    print("Connexion OK :", result["ok"] == 1)
driver.close()
```

---

## Trouver vos credentials AuraDB

1. Se connecter sur [console.neo4j.io](https://console.neo4j.io).
2. Sélectionner votre instance.
3. Cliquer sur **Connect** → les informations de connexion y sont affichées.
4. Le mot de passe n'est visible qu'une seule fois à la création — si perdu,
   utiliser **Reset password** dans la console.
