---
title: Accueil
layout: default
nav_order: 4
---

## Objectif

Ce script permet d’extraire automatiquement la liste des films du Marvel Cinematic Universe (MCU) depuis Wikipédia, puis de générer un fichier CSV contenant les films déjà sortis et leur année de sortie.

Il sert de source de référence fiable pour identifier les films Marvel dans un pipeline de données, et ensuite faire une jointure avec les tables IMDb.

## Fonctionnement 

Le script :

-  Récupère la page Wikipédia des films MCU
- Extrait les tableaux HTML présents dans la page
- Sélectionne ceux contenant une colonne Film
- Nettoie les titres et les dates (suppression des références Wikipédia, espaces, etc.)
- Filtre uniquement les films déjà sortis
- Extrait l’année de sortie
- exporte le résultat en CSV

## Entrée

Source :
https://en.wikipedia.org/wiki/List_of_Marvel_Cinematic_Universe_films

## Sortie

Fichier généré :

data/raw/marvel_films.csv

Contenu :

| film         | release_year |
|--------------|--------------|
| Iron Man     | 2008         |
| The Avengers | 2012         |


## Logique d’extraction

Le script s’appuie sur la structure des tableaux Wikipédia (via pandas.read_html).

## Utilisation

Lancer :

- python read_marvel_wiki.py

- Vérifier que le dossier data/raw/ existe avant exécution.
