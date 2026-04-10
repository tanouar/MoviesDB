---
title: Guide du script run_pipeline.py
layout: default
nav_order: 3
---

# Utilisation du script `run_pipeline.py`

Le script `run_pipeline.py` est le point d'entrée principal du pipeline ETL. Il orchestre le téléchargement des données IMDb, la création de la base MySQL dans un conteneur Docker, l'exécution des requêtes SQL d'extraction Marvel, et la génération des fichiers CSV de sortie.

## Prérequis

Avant de lancer le script, les éléments suivants doivent être installés et configurés :

- **Python 3.x** avec les dépendances du projet installées
- **Docker** et **Docker Compose** installés et le démon Docker en cours d'exécution
- Un fichier **`.env`** à la racine du projet (voir section Configuration)

### Installation des dépendances Python

```bash
pip install -r requirements.txt
```

Les principales dépendances utilisées par le pipeline sont : `pandas`, `requests`, `python-dotenv`.

## Configuration

Le script utilise des variables d'environnement pour la connexion MySQL. Créez un fichier `.env` à la racine du projet. Un exemple est disponible dans `.env.example` :

```bash
cp .env.example .env
```

Puis éditez le fichier `.env` avec vos valeurs :

```
MYSQL_ROOT_PASSWORD=votre_mot_de_passe
MYSQL_DATABASE=IMDb
MYSQL_USER=votre_utilisateur
MYSQL_PASSWORD=votre_mot_de_passe
```

> La variable `MYSQL_ROOT_PASSWORD` est **obligatoire**. Le script échouera avec une erreur si elle n'est pas définie.

## Lancement

Le script se lance depuis le répertoire `pipeline/` :

```bash
cd pipeline
python run_pipeline.py
```

### Arguments en ligne de commande

| Argument | Forme courte | Description |
|----------|-------------|-------------|
| `--debug` | `-d` | Active les logs en mode DEBUG (plus verbeux) |
| `--createdb` | `-db` | Crée la base de données et les tables uniquement |
| `--runqueries` | `-q` | Exécute les requêtes SQL d'extraction Marvel uniquement |
| `--createcsvs` | `-csv` | Génère les fichiers CSV à partir des données existantes |

> **Comportement par défaut :** si aucun argument n'est passé, les trois étapes (`-db`, `-q`, `-csv`) sont exécutées automatiquement.

### Exemples d'utilisation

**Exécution complète du pipeline :**
```bash
python run_pipeline.py
```

**Exécution complète avec logs détaillés :**
```bash
python run_pipeline.py -d
```

**Créer uniquement la base de données :**
```bash
python run_pipeline.py -db
```

**Exécuter uniquement les requêtes Marvel et générer les CSV :**
```bash
python run_pipeline.py -q -csv
```

## Étapes du pipeline

Le pipeline se déroule en trois grandes phases, chacune contrôlable via les arguments :

### Phase 1 — Création de la base de données (`-db`)

1. **Démarrage du conteneur Docker MySQL** via Docker Compose (`docker/docker-compose.yml`)
2. **Téléchargement des fichiers IMDb** depuis `datasets.imdbws.com` :
   - `name.basics.tsv.gz` — données des personnes (acteurs, réalisateurs, etc.)
   - `title.basics.tsv.gz` — données des titres (films, séries)
   - `title.episode.tsv.gz` — données des épisodes
   - `title.principals.tsv.gz` — casting et équipe technique
   - `title.ratings.tsv.gz` — notes et votes
3. **Extraction des fichiers `.gz`** en fichiers `.tsv`
4. **Copie des fichiers TSV** dans le conteneur Docker
5. **Exécution des scripts SQL** de configuration (dans l'ordre) :
   - `imdb_create_db.sql` — création de la base de données
   - `imdb_create_tables.sql` — création des tables
   - `imdb_load_data.sql` — chargement des données TSV
   - `imdb_add_constraints.sql` — ajout des contraintes
   - `imdb_add_index.sql` — création des index
   - `create_movies_table.sql` — table additionnelle des films

> Les fichiers déjà téléchargés ou extraits sont automatiquement ignorés pour éviter les téléchargements inutiles.

### Phase 2 — Exécution des requêtes Marvel (`-q`)

1. Suppression des anciens fichiers CSV dans le conteneur
2. Exécution de toutes les requêtes SQL du dossier `mysql/` correspondant au pattern `*marvel*.sql` :
   - `marvel_movies.sql` — films Marvel
   - `marvel_actors.sql` — acteurs Marvel
   - `marvel_characters.sql` — personnages
   - `marvel_actors_characters.sql` — relation acteur-personnage
   - `marvel_character_appears_in_movie.sql` —  personnages dans les films
   - `marvel_directors_movies.sql` — réalisateurs
   - `marvel_producers_movies.sql` — producteurs

Les résultats sont exportés en CSV dans le dossier `data/tests/`.

### Phase 3 — Mise en forme des CSV (`-csv`)

1. Lecture de chaque fichier CSV Marvel généré
2. Ajout des en-têtes de colonnes appropriés selon le type de fichier
3. Réécriture du fichier CSV avec les en-têtes

## Fichiers de sortie

Les fichiers CSV générés se trouvent dans `data/tests/` :

| Fichier | Colonnes |
|---------|----------|
| `*movies*.csv` | `title_id`, `primary_title`, `genres`, `start_year`, `runtime_minutes` |
| `*actors*.csv` | `person_id`, `person_name`, `born`, `died` |
| `*characters*.csv` | `character_name` |
| `*character_appears_in_movie*.csv` | `title_id`, `character_name` |
| `*person_directs_movie*.csv` | `title_id`, `person_id` |
| `*person_produces_movie*.csv` | `person_id`, `title_id` |
| `*person_plays_character*.csv` | `person_id`, `character_name` |

## Logs

Le pipeline génère des logs dans deux destinations :

- **Console** — affichage en temps réel de la progression
- **Fichier** — `pipeline/pipeline.log` (mode ajout)

Le format des logs est : `YYYY-MM-DD HH:MM - NIVEAU - Message`

Utilisez l'option `-d` pour activer le mode DEBUG avec des informations plus détaillées (aperçu des DataFrames, détails des commandes exécutées, etc.).

## Dépannage

### Le script échoue avec `Missing required environment variable: MYSQL_ROOT_PASSWORD`
Vérifiez que le fichier `.env` existe à la racine du projet et qu'il contient la variable `MYSQL_ROOT_PASSWORD`.

### Erreur de connexion Docker
Assurez-vous que le démon Docker est en cours d'exécution :
```bash
docker info
```

### Les fichiers CSV sont vides
Vérifiez que la phase de création de la base (`-db`) a été exécutée au préalable. Les requêtes Marvel nécessitent que les données IMDb soient déjà chargées.

### Erreur lors du chargement des données SQL
Le conteneur MySQL peut mettre quelques secondes à démarrer. Le script attend jusqu'à 30 secondes que le socket MySQL soit disponible. Si le problème persiste, vérifiez les logs Docker :
```bash
docker logs moviesdb_mysql
```

## Nettoyage

À la fin de l'exécution (succès ou échec), le script arrête automatiquement le conteneur Docker via `docker compose down`. Les données MySQL sont persistées dans un volume Docker (`mysql_data`) et seront disponibles lors de la prochaine exécution.

Pour supprimer complètement les données et repartir de zéro :
```bash
docker compose -f docker/docker-compose.yml down -v
```
