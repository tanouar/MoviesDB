"""
Script pour charger les données Marvel dans Neo4j AuraDB
Utilise les fichiers CSV du dossier data/tests/
"""
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

from pipeline_logger import setup_logger


logger = logging.getLogger("imdb_pipeline.load_auradb")

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "tests"

# Charger les variables d'environnement depuis .env
load_dotenv(PROJECT_ROOT / ".env")

# Paramètres de connexion AuraDB
# Définir ces valeurs directement ici, soit les définir dans le fichier .env
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://xxxxxxxx.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password-here")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
AURA_INSTANCEID = os.getenv("AURA_INSTANCEID", "")
AURA_INSTANCENAME = os.getenv("AURA_INSTANCENAME", "")


def check_credentials():
    """Vérifie que les identifiants AuraDB sont configurés"""
    if not NEO4J_PASSWORD or NEO4J_PASSWORD == "your-password-here":
        logger.error("Veuillez configurer vos identifiants AuraDB")
        logger.error("\nOptions:")
        logger.error(
            "1. Créez/modifiez le fichier .env avec:"
        )
        logger.error("   NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io")
        logger.error("   NEO4J_USERNAME=neo4j")
        logger.error("   NEO4J_PASSWORD=votre-mot-de-passe")
        logger.error("   NEO4J_DATABASE=neo4j")
        logger.error("   AURA_INSTANCEID=xxxxxxxx")
        logger.error("   AURA_INSTANCENAME=nom-de-votre-instance")
        logger.error(
            "2. Ou modifiez directement les variables dans ce script"
        )
        sys.exit(1)


def connect_to_auradb():
    """Se connecte à Neo4j AuraDB"""
    logger.info("Connexion à Neo4j AuraDB...")
    logger.info(f"  URI: {NEO4J_URI}")
    logger.info(f"  Database: {NEO4J_DATABASE}")
    logger.info(f"  Instance: {AURA_INSTANCENAME} ({AURA_INSTANCEID})")

    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

        # Test de connexion
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("RETURN 1 as test")
            result.single()

        logger.info("Connexion réussie à AuraDB")
        return driver

    except Exception as e:
        logger.error(f"Erreur de connexion à AuraDB: {e}")
        logger.error("Vérifiez:")
        logger.error("  - Votre URI Neo4j (doit commencer par neo4j+s://)")
        logger.error("  - Votre nom d'utilisateur et mot de passe")
        logger.error("  - Que votre instance AuraDB est bien démarrée")
        sys.exit(1)


def clean_constraints(session):
    """Supprime toutes les contraintes existantes"""
    logger.info("Suppression des contraintes existantes...")

    result = session.run("SHOW CONSTRAINTS")
    constraints = list(result)

    if constraints:
        logger.info(f"  {len(constraints)} contrainte(s) trouvée(s)")
        for constraint in constraints:
            constraint_name = constraint.get('name')
            if constraint_name:
                try:
                    session.run(f"DROP CONSTRAINT {constraint_name}")
                    logger.debug(
                        f"  Contrainte '{constraint_name}' supprimée"
                    )
                except Exception as e:
                    logger.warning(
                        f"  Impossible de supprimer '{constraint_name}': {e}"
                    )
    else:
        logger.info("  Aucune contrainte existante")

    logger.info("Contraintes vérifiées")


def clean_indexes(session):
    """Supprime tous les index existants (sauf LOOKUP)"""
    logger.info("Suppression des index existants...")

    result = session.run("SHOW INDEXES")
    indexes = list(result)

    if indexes:
        logger.info(f"  {len(indexes)} index trouvé(s)")
        for index in indexes:
            index_name = index.get('name')
            index_type = index.get('type', '')
            # Ne pas supprimer les index LOOKUP (système)
            if index_name and 'LOOKUP' not in index_type.upper():
                try:
                    session.run(f"DROP INDEX {index_name}")
                    logger.debug(f"  Index '{index_name}' supprimé")
                except Exception as e:
                    logger.warning(
                        f"  Impossible de supprimer '{index_name}': {e}"
                    )
    else:
        logger.info("  Aucun index existant")

    logger.info("Index vérifiés")


def delete_all_data(session):
    """Supprime toutes les données de la base"""
    logger.info("Suppression des données précédentes...")

    query = 'MATCH (n) DETACH DELETE n'
    session.run(query)

    logger.info("Données supprimées")


def load_characters(session, data_dir):
    """Charge les personnages Marvel"""
    logger.info("Chargement des personnages...")

    characters_df = pd.read_csv(data_dir / "marvel_characters.csv")
    logger.info(f"  {len(characters_df)} personnages à charger")

    for _, row in characters_df.iterrows():
        query = 'CREATE (:Character {name: $name})'
        session.run(query, name=row['character_name'])

    logger.info("Personnages chargés")
    return characters_df


def load_people(session, data_dir):
    """Charge les personnes (acteurs/réalisateurs/producteurs)"""
    logger.info("Chargement des personnes...")

    actors_df = pd.read_csv(data_dir / "marvel_actors.csv")
    logger.info(f"  {len(actors_df)} personnes à charger")

    for _, row in actors_df.iterrows():
        # Gérer les valeurs \N (NULL dans les CSV IMDb)
        birth_year = (
            None if pd.isna(row['born']) or row['born'] == '\\N'
            else int(row['born'])
        )
        death_year = (
            None if pd.isna(row['died']) or row['died'] == '\\N'
            else int(row['died'])
        )

        query = '''
        CREATE (:Person {
            id: $id,
            name: $name,
            birth_year: $birth_year,
            death_year: $death_year
        })
        '''
        session.run(
            query,
            id=row['person_id'],
            name=row['person_name'],
            birth_year=birth_year,
            death_year=death_year
        )

    logger.info("Personnes chargées")
    return actors_df


def load_movies(session, data_dir):
    """Charge les films Marvel"""
    logger.info("Chargement des films...")

    movies_df = pd.read_csv(data_dir / "marvel_movies.csv")
    logger.info(f"  {len(movies_df)} films à charger")

    for _, row in movies_df.iterrows():
        query = '''
        CREATE (:Movie {
            id: $id,
            title: $title,
            year: $year,
            runtime: $runtime,
            genres: $genres
        })
        '''
        session.run(
            query,
            id=row['title_id'],
            title=row['primary_title'],
            year=(
                int(row['start_year'])
                if not pd.isna(row['start_year']) else None
            ),
            runtime=(
                int(row['runtime_minutes'])
                if not pd.isna(row['runtime_minutes']) else None
            ),
            genres=(
                row['genres'].split(',')
                if pd.notna(row['genres']) else []
            )
        )

    logger.info("Films chargés")
    return movies_df


def create_relationships(session, data_dir):
    """Crée toutes les relations entre les entités"""
    logger.info("Création des relations...")

    stats = {}

    # Relations acteur-personnage
    logger.info("  Chargement des relations acteur-personnage...")
    plays_df = pd.read_csv(data_dir / "marvel_person_plays_character.csv")
    logger.info(f"    {len(plays_df)} relations à créer")

    for _, row in plays_df.iterrows():
        query = '''
        MATCH (p:Person {id: $person_id})
        MATCH (c:Character {name: $character_name})
        CREATE (p)-[:PLAY]->(c)
        WITH p
        SET p:Actor
        '''
        session.run(
            query,
            person_id=row['person_id'],
            character_name=row['character_name']
        )

    logger.info("  Relations acteur-personnage créées")
    stats['plays'] = len(plays_df)

    # Apparitions de personnages
    logger.info("  Chargement des apparitions de personnages...")
    appears_df = pd.read_csv(
        data_dir / "marvel_character_appears_in_movie.csv"
    )
    logger.info(f"    {len(appears_df)} apparitions à créer")

    for _, row in appears_df.iterrows():
        query = '''
        MATCH (c:Character {name: $character_name})
        MATCH (m:Movie {id: $title_id})
        CREATE (c)-[:APPEAR_IN]->(m)
        '''
        session.run(
            query,
            character_name=row['character_name'],
            title_id=row['title_id']
        )

    logger.info("  Apparitions créées")
    stats['appears'] = len(appears_df)

    # Relations réalisateur-film
    logger.info("  Chargement des relations réalisateur-film...")
    directs_df = pd.read_csv(data_dir / "marvel_person_directs_movie.csv")
    logger.info(f"    {len(directs_df)} relations à créer")

    for _, row in directs_df.iterrows():
        query = '''
        MATCH (p:Person {id: $person_id})
        MATCH (m:Movie {id: $title_id})
        CREATE (p)-[:DIRECTED]->(m)
        '''
        session.run(
            query,
            person_id=row['person_id'],
            title_id=row['title_id']
        )

    logger.info("  Relations réalisateur-film créées")
    stats['directs'] = len(directs_df)

    # Relations producteur-film
    logger.info("  Chargement des relations producteur-film...")
    produces_df = pd.read_csv(data_dir / "marvel_person_produces_movie.csv")
    logger.info(f"    {len(produces_df)} relations à créer")

    for _, row in produces_df.iterrows():
        query = '''
        MATCH (p:Person {id: $person_id})
        MATCH (m:Movie {id: $title_id})
        CREATE (p)-[:PRODUCED]->(m)
        '''
        session.run(
            query,
            person_id=row['person_id'],
            title_id=row['title_id']
        )

    logger.info("  Relations producteur-film créées")
    stats['produces'] = len(produces_df)

    return stats


def create_indexes(session):
    """Crée les index pour améliorer les performances"""
    logger.info("Création des index...")

    indexes = [
        (
            "CREATE INDEX character_name_index IF NOT EXISTS "
            "FOR (c:Character) ON (c.name)"
        ),
        (
            "CREATE INDEX person_id_index IF NOT EXISTS "
            "FOR (p:Person) ON (p.id)"
        ),
        (
            "CREATE INDEX movie_id_index IF NOT EXISTS "
            "FOR (m:Movie) ON (m.id)"
        ),
        (
            "CREATE INDEX movie_title_index IF NOT EXISTS "
            "FOR (m:Movie) ON (m.title)"
        )
    ]

    for index_query in indexes:
        try:
            session.run(index_query)
            logger.debug("  Index créé")
        except Exception as e:
            logger.warning(f"  Erreur lors de la création d'index: {e}")

    logger.info("Index créés")


def main():
    """Point d'entrée principal du script"""
    logger = setup_logger(level=logging.INFO)

    logger.info("=== Chargement des données Marvel dans Neo4j AuraDB ===")
    logger.info(f"URI: {NEO4J_URI}")
    logger.info(f"Source des données: {DATA_DIR}")

    # Vérifier les identifiants
    check_credentials()

    # Connexion à AuraDB
    driver = connect_to_auradb()

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            # Nettoyage
            clean_constraints(session)
            clean_indexes(session)
            delete_all_data(session)

            # Chargement des données
            characters_df = load_characters(session, DATA_DIR)
            actors_df = load_people(session, DATA_DIR)
            movies_df = load_movies(session, DATA_DIR)

            # Création des relations
            rel_stats = create_relationships(session, DATA_DIR)

            # Création des index
            create_indexes(session)

        # Statistiques finales
        logger.info("=== Chargement terminé avec succès ===")
        logger.info("Statistiques:")
        logger.info(f"  - {len(characters_df)} personnages")
        logger.info(f"  - {len(actors_df)} personnes")
        logger.info(f"  - {len(movies_df)} films")
        logger.info(f"  - {rel_stats['plays']} relations acteur-personnage")
        logger.info(f"  - {rel_stats['appears']} apparitions")
        logger.info(f"  - {rel_stats['directs']} réalisateur-film")
        logger.info(f"  - {rel_stats['produces']} producteur-film")
        logger.info("Accédez à https://console.neo4j.io")

    except Exception as e:
        logger.error(f"Erreur lors du chargement: {e}", exc_info=True)
        return 1

    finally:
        driver.close()
        logger.info("Connexion fermée")

    return 0


if __name__ == "__main__":
    exit(main())
