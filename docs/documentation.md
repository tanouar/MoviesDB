---
title: Documentation du projet
layout: default
nav_order: 1
---
# Mise en place de l’environnement

## Installation des dépendances (`requirements.txt`)

- Erreur rencontrée lors de la compilation de `pysqlite3` sur macOS  
  - Cause probable : Python est déjà compilé avec SQLite sur macOS
  - Solution : commenter ou supprimer la ligne `import pysqlite3`
  - Utiliser le module standard `sqlite3` à la place

---

# Structure actuelle des dossiers

```text
.
├── data
│   ├── db
│   ├── raw
│   └── tests
├── docker
├── docs
├── notebooks
├── requirements.txt
├── tests
└── venv
```

# Chargement et transformation des données

## Création du notebook de chargement

- Création du notebook `Create_SQlite_Database.ipynb` pour charger les fichiers TSV IMDb
- Implémentation d’une fonction générique `Load_Table_From_TSV` permettant :
  - le nettoyage des données
  - la création des tables
  - la construction de la base SQLite 

---

# Nettoyage des données TSV

## Étapes de préparation et de nettoyage

- Inspection des tables générées à partir des fichiers TSV bruts
- Création d’une base SQLite (`.db`) à partir des données sources
- Traitement des valeurs manquantes (`\N`), notamment dans la table `crew`, via des scripts Python afin de garantir l’utilisation de `NULL` 

---

# Méthode 
- Télécharger les données TSV (Lancer la première )

- Importer les données dans une BDD MYSQL dans Docker avec le script `notebooks/Create_MySQL_Database.ipynb`

- Lancer le script python pour executer les commandes docker dans le notebook suivant : `notebooks/Run_SQL_Queries.ipynb`


# Étapes d’importation

- Définition explicite de la longueur des champs de type `String` pour assurer une conversion correcte en `VARCHAR(n)` et la compatibilité avec MySQL
- Génération d’un fichier SQL (`newIMDB.sql`) à partir de la base SQLite  
  *(export réalisé via DB Browser for SQLite)*

## Limitation d'importation de fichier SQL

- **Taille du fichier SQL** : ~19 Go  
- **Mémoire disponible** : 8 Go de RAM  
- **Conséquence** : impossibilité de manipuler ou d’importer le fichier SQL 

## Approche 1 : Créer un fichier SQlite (.db) à partir des TSV avec Python et l'importer dans Docker  

- Utilisation directe de SQLite dans un conteneur Docker afin d’éviter la génération d’un fichier SQL massif
- Création d’un volume Docker pour assurer la persistance des données
- Exécution des requêtes SQL directement via `sqlite3` dans le conteneur

## Exécution de SQLite en mode interactif

```bash
docker exec -it moviesdb_sqlite sqlite3 /data/newIMDB.db

```
NB- ctrl d pour quitter 

## Pour utiliser un fichier sql avec des requêtes

```bash
docker exec -i $CONTAINER sqlite3 /data/newIMDB.db ".read /tmp/marvel_queries.sql"
```

## Pour formatter une table dans SQLite

```bash
.mode column
.headers on
```

## Pour exécuter les requêtes et sauvegarder données en tant que fichier csv

```bash
docker exec $CONTAINER sqlite3 /data/newIMDB.db \
  ".headers on" ".mode csv" \
  ".output $CONTAINER_FILE_PATH/nom_du_fichier.csv" \
  "SELECT primary_title, rating, votes FROM titles JOIN ratings ON titles.title_id = ratings.title_id WHERE LOWER(primary_title) LIKE '%marvel%';" \
  ".output stdout"
```

### Limitations 

- Besoin d'écrire des requêtes pour chercher des patterns dans les titres de fimls Marvel 
- On ne peut pas utiliser REGEXP directement avec SQlite
- Il nous faut une version SQL 


## Approche 2 :  Conversion de fichiers TSV en BDD MYSQL 


- Utilisation de MYSQL dans un conteneur Docker
- Conversion de fichiers TSV en BDD MYSQL directement, sans passer par SQlite
- Adaptation d'un script provenant de github pour créer les tables et utiliser les fichiers TSV pour charger les données:
https://github.com/dlwhittenbury/MySQL_IMDb_Project 


### Copier les fichiers pour créer et charger les données dans un dossier /tmp/

Définir les variables suivantes pour faciliter la réutilisation des chemins et noms de conteneurs :

```bash
CONTAINER=moviesdb_mysql
CSV_HOST_PATH=data/tests
SQL_FILE_PATH=utils
CONTAINER_FILE_PATH=/tmp/
```

Utiliser ces variables dans les commandes :

```bash
docker cp data/raw/ $CONTAINER:/tmp/raw/
docker cp mysql/imdb-create-tables.sql $CONTAINER:/tmp/
docker cp mysql/imdb-load-data.sql $CONTAINER:/tmp/
docker exec -it $CONTAINER mysql -u root -p --local-infile IMDb
```

#### Commandes MYSQL utilisées
```bash
SOURCE /tmp/imdb-create-tables.sql
SOURCE /tmp/imdb-load-data.sql
SOURCE /tmp/imdb-add-constraints.sql
SOURCE /tmp/imdb-add-index.sql
SOURCE /tmp/marvel_movies.sql
```
- Copier le script des requêtes dans le conteneur et exécuter le script

```bash
docker cp ${SQL_FILE_PATH}/marvel_movies.sql $CONTAINER:/tmp/
SOURCE /tmp/marvel_movies.sql
```

- Convertir les résultats et exporter en tant que CSV 

```bash
docker cp $CONTAINER:/tmp/marvel_movies.csv ${CSV_HOST_PATH}/marvel_movies.csv
```
---

# Exécuter le script dans le dossier pipeline (Run_pipeline.py) pour créer la base, charger les données, et lancer les requêtes sql 

## Rajouter un fichier .env dans le dossier racine avec les identifiants:

Exemple: 
```bash
MYSQL_ROOT_PASSWORD=changeme
MYSQL_DATABASE=IMDb
MYSQL_USER=appuser
MYSQL_PASSWORD=changeme

```
## Logging 
### Logging avec la lib logging et une structure try & except pour catché les erreurs + mise en place de 4 niveaux de logs : INFO, WARNING, ERROR, DEBUG

### Le script prendre en argument -d pour activer le mode DEBUG, -db pour créer la base de donnée et -csv pour créer les csv

---

# Application Streamlit — Exploration du graphe MCU

L'application Streamlit permet d'explorer interactivement le graphe Marvel Cinematic Universe stocké dans Neo4j ou AuraDB.

## Prérequis

- Neo4j local (Docker) ou AuraDB opérationnel avec les données chargées
- Python 3.10+
- Variables d'environnement configurées (fichier `.env` dans `Streamlit-App/`)

## Configuration

Créer un fichier `.env` dans le dossier `Streamlit-App/` :

```env
NEO4J_URI=bolt://localhost:7687        # ou neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=votre-mot-de-passe
```

## Installation et lancement

```bash
cd Streamlit-App
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`.

## Fonctionnalités

### Graphe interactif

- Visualisation des nœuds et relations du graphe MCU via **PyVis**
- Thème visuel **Avengers: Doomsday** (CSS personnalisé)
- Compte à rebours jusqu'à la sortie du film (16 décembre 2026)

### Filtres (barre latérale)

| Filtre | Description |
|--------|-------------|
| **Labels** | Sélectionner les types de nœuds à afficher (`Person`, `Movie`, `Character`) |
| **Types de relations** | Filtrer les relations (`PLAY`, `APPEAR_IN`, `DIRECTED`, `PRODUCED`) |
| **Film** | Afficher le sous-graphe centré sur un film spécifique |
| **Rafraîchir** | Vider le cache et recharger les données depuis Neo4j |

### Mode Analyse topologique

Activé via le toggle **"Mode Analyse (Betweenness Centrality)"** dans la sidebar.

#### Betweenness Centrality (BC)

- Calcule l'importance de chaque nœud comme pont dans le réseau
- Les nœuds dépassant le **seuil BC** sont mis en évidence en vert (`#296218`)
- Paramètre **Seuil BC minimum** (0.0 → 1.0, pas 0.01)
- Paramètre **Top N nœuds ponts** (3 → 30)

#### Détection de communautés

Sélection de l'algorithme via le sélecteur :

| Algorithme | Description |
|-----------|-------------|
| **Louvain** | Optimisation de la modularité (recommandé) |
| **Greedy Modularity** | Fusion gloutonne de communautés |
| **Label Propagation** | Propagation d'étiquettes (rapide) |
| **Girvan-Newman** | Suppression d'arêtes (lent sur grands graphes) |

Les communautés sont colorées automatiquement dans le graphe.

#### Tableau Top-N nœuds ponts

Affiché sous le graphe en mode Analyse — liste les nœuds les plus centraux avec leur score BC.

### Cache

Toutes les requêtes Neo4j sont mises en cache via `st.cache_data` :
- Labels et types de relations : TTL 300 secondes
- Films : TTL 300 secondes
- Graphe filtré : TTL 120 secondes
- Analyse topologique : cache permanent jusqu'au rafraîchissement

## Structure du code

```text
Streamlit-App/
├── app.py                  # Point d'entrée principal
├── requirements.txt        # Dépendances Python
├── config.toml             # Configuration du thème Streamlit
├── assets/
│   ├── css/avengers.css    # Thème visuel
│   ├── style.grass         # Style Neo4j Browser
│   └── components/
│       └── countdown.html  # Compte à rebours HTML/JS
└── modules/
    ├── neo4j_connector.py  # Connexion et requêtes Neo4j
    ├── graph_builder.py    # Construction du graphe PyVis
    ├── graph_analyzer.py   # Analyse topologique (BC, communautés)
    └── ui_helpers.py       # Composants UI (sidebar)
```


