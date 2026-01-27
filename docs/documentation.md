# Nettoyage des données TSV

## Étapes de préparation et de nettoyage
- Inspecter les tables créées à partir des fichiers TSV dans SQLite
- Créer une version SQLite (`.db`) propre à partir des données brutes
- Adapter les types de données pour assurer la compatibilité SQL
- Traiter les valeurs manquantes (`\\N`), en particulier dans la table `crew`

---

# Conversion et import dans MySQL

## Étapes d’importation
- Générer un fichier SQL (`dump.sql`) à partir de la base SQLite
- Ajouter explicitement une longueur aux champs de type String pour une conversion en `VARCHAR(n) ` afin d’assurer la compatibilité avec MySQL



