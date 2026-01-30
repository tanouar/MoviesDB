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

- Création du notebook `IMDB_Database_Creation.ipynb` pour charger les fichiers TSV IMDb
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

# Conversion et import dans MySQL

## Étapes d’importation

- Définition explicite de la longueur des champs de type `String` pour assurer une conversion correcte en `VARCHAR(n)` et la compatibilité avec MySQL
- Génération d’un fichier SQL (`newIMDB.sql`) à partir de la base SQLite  
  *(export réalisé via DB Browser for SQLite)*

## Limitation rencontrée

- **Taille du fichier SQL** : ~19 Go  
- **Mémoire disponible** : 8 Go de RAM  
- **Conséquence** : impossibilité de manipuler ou d’importer le fichier SQL 

---

# Alternative : utilisation de SQLite dans Docker

## Approche retenue

- Utilisation directe de SQLite dans un conteneur Docker afin d’éviter la génération d’un fichier SQL massif
- Création d’un volume Docker pour assurer la persistance des données
- Exécution des requêtes SQL directement via `sqlite3` dans le conteneur

---

# Commandes Docker utilisées

## Script python pour executer les commandes docker dans le notebook suivant : notebooks/run_sqlite_pipeline.ipynb

### Description des commandes utilisées 

- Scripts Bash pour gérer le conteneur SQLite

### `start_sqlite.sh`
```bash
docker compose -f docker/docker-compose-sqlite.yml up -d --build
```
### `stop_sqlite.sh`
```bash
docker stop moviesdb_sqlite
docker compose -f docker/docker-compose-sqlite.yml down
```
### Copie de la base SQLite dans le conteneur

```bash
docker cp notebooks/data/db/newIMDB.db moviesdb_sqlite:/data/newIMDB.db
```

### Exécution de SQLite en mode interactif

```bash
docker exec -it moviesdb_sqlite sqlite3 /data/newIMDB.db
ctrl d pour quitter sqlite interactif
```

### Pour utiliser un fichier sql avec des requêtes

```bash
docker cp utils/marvel_queries.sql moviesdb_sqlite:/data/marvel_queries.sql

.read /data/marvel_queries.sql
ou 
docker exec -i moviesdb_sqlite sqlite3 /data/newIMDB.db ".read /data/marvel_queries.sql"
```

### Pour formatter une table dans SQlite

```bash
.mode column
.headers on
```

### Pour executer les requêtes et sauvegarder données en tant que fichier csv
```bash
docker exec moviesdb_sqlite sqlite3 /data/newIMDB.db \
  ".headers on" ".mode csv" \
  ".output /data/nom_du_fichier.csv" \
  "SELECT primary_title, rating, votes FROM titles JOIN ratings ON titles.title_id = ratings.title_id WHERE LOWER(primary_title) LIKE '%marvel%';" \
  ".output stdout"
```bash
