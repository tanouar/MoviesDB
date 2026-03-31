---
title: Accueil
layout: default
nav_order: 0
---

# MoviesDB — Documentation

Bienvenue sur la documentation du projet **MoviesDB**, une application d'exploration du Marvel Cinematic Universe via un graphe de connaissances Neo4j.

## Pages disponibles

| Page | Description |
|------|-------------|
| [Documentation](documentation) | Mise en place de l'environnement, chargement des données, pipeline |
| [Guide Neo4j](neo4j-scripts-guide) | Scripts de chargement, modèle de données, résolution d'erreurs |
| [Script run_pipeline.py](Utilisation-script-run_pipeline) | Pipeline ETL complet : arguments, étapes, fichiers de sortie, dépannage |
| [Schéma IMDb](imdb-schema) | Diagramme relationnel et description des tables de la base MySQL |

## Architecture du projet

```text
MoviesDB/
├── data/           # Données brutes (TSV IMDb, CSV Marvel)
├── docker/         # Docker Compose (MySQL, SQLite)
├── docs/           # Documentation (ce site)
├── mysql/          # Scripts SQL MySQL
├── notebooks/      # Notebooks Jupyter
├── pipeline/       # Scripts Python de chargement Neo4j/AuraDB
├── Streamlit-App/  # Application de visualisation du graphe
└── tests/          # Tests unitaires (pytest)
```

## Auteurs

- **Tarik ANOUAR** — [LinkedIn](https://www.linkedin.com/in/anouartarik)
- **Vaynee SUNGEELEE** — [LinkedIn](https://www.linkedin.com/in/vaynee-sungeelee/)
