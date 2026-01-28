# Nettoyage des données TSV

## Étapes de préparation et de nettoyage

- Inspection des tables créées à partir des fichiers TSV bruts (IMDb) dans SQLite  
- Création d’une base SQLite propre (`.db`) à partir des données sources  
- Traitement des valeurs manquantes (`\N`), en particulier dans la table `crew`, via des scripts Python afin de garantir des `NULL` réels en base  

---

# Conversion et import dans MySQL

## Étapes d’importation

- Définition explicite de la longueur des champs de type `String` pour une conversion correcte en `VARCHAR(n)` et une compatibilité MySQL
- Génération d’un fichier SQL (`newIMDB.sql`) à partir de la base SQLite (export via **DB Browser for SQLite**)
- Limitation rencontrée :  
  - fichier SQL ~19 Go  
  - machine avec 8 Go de RAM  
  - impossibilité de manipuler ou d’importer le fichier SQL de manière fiable

---

# Alternative : utilisation de SQLite dans Docker

## Approche retenue

- Utilisation de SQLite directement dans un conteneur Docker afin d’éviter la génération d’un fichier SQL massif
- Création d’un volume Docker pour assurer la persistance des données
- Copie du fichier SQLite dans le conteneur et exécution des requêtes via `sqlite3`

## Commandes utilisées

```bash
docker cp notebooks/data/titles.sql moviesdb_sqlite:/data/newIMDB.db
docker exec -it moviesdb_sqlite ls -l /data
docker exec -it moviesdb_sqlite sqlite3 /data/newIMDB.db
