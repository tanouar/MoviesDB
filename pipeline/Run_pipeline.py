import subprocess
import time
from pathlib import Path
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import gzip
import logging
from pipeline_logger import setup_logger

logger = logging.getLogger("imdb_pipeline.run_pipeline")

# Config
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
COMPOSE_FILE = PROJECT_ROOT / "docker" / "docker-compose.yml"
SQL_DIR = PROJECT_ROOT / "mysql"
DATA_DIR = PROJECT_ROOT / "data" / "tests"
CONTAINER = "moviesdb_mysql"
DB = "IMDb"
DOCKER = "docker"
MYSQL_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")

if not MYSQL_PASSWORD:
    logger.error(
        "MYSQL_ROOT_PASSWORD not set.\n"
        "Create a .env file in project root.\n"
        "See .env.example for required variables."
    )
    raise RuntimeError("Missing required environment variable: MYSQL_ROOT_PASSWORD")

env = os.environ.copy()
env["MYSQL_PWD"] = MYSQL_PASSWORD

# functions


def run_command(cmd, check=True):
    """Run command"""
    logger.info(f"\nRunning: {' '.join(map(str, cmd))}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.warning("STDOUT:\n%s", result.stdout)
        logger.warning("STDERR:\n%s", result.stderr)
        if check:
            logger.error(f"Command failed with exit code {result.returncode}")
            raise RuntimeError(
                f"Command failed with exit code {result.returncode}"
            )

    return result


def download_files():
    # Importer les données IMDB
    urls = ['https://datasets.imdbws.com/name.basics.tsv.gz',
            'https://datasets.imdbws.com/title.basics.tsv.gz',
            'https://datasets.imdbws.com/title.episode.tsv.gz',
            'https://datasets.imdbws.com/title.principals.tsv.gz',
            'https://datasets.imdbws.com/title.ratings.tsv.gz']

    # telechargement des fichiers
    for url in urls:
        filename = url.split('/')[-1]
        target_path = PROJECT_ROOT / "data" / "raw" / filename
        logger.info(target_path)

        if target_path.exists():
            logger.info("File %s already exists. Skipping download.", target_path)
        else:
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                with open(target_path, 'wb') as f:
                    f.write(response.raw.read())

        if target_path.suffix == ".gz":
            tsv_path = target_path.with_suffix("")

        with gzip.open(target_path, 'rb') as gz_file:
            if tsv_path.exists():
                logger.info("File %s already exists. Skipping extraction.", tsv_path)
            else:
                logger.info("Extracting file to %s", tsv_path)
                with open(tsv_path, 'wb') as f:
                    f.write(gz_file.read())
                logger.info("Extraction completed for %s", tsv_path)

def copy_tsv_to_container():
    file_names = [
        "name.basics.tsv",
        "title.basics.tsv",
        "title.episode.tsv",
        "title.principals.tsv",
        "title.ratings.tsv"]

    for file in file_names:
        logger.info(f"Copying {file} into docker container")
        result = subprocess.run(["docker",
                                 "cp",
                                 f"{PROJECT_ROOT}/data/raw/{file}",
                                 f"{CONTAINER}:/tmp/{file}"],
                                capture_output=True,
                                text=True,
                                check=False)
        logger.debug(result.stderr)

def execute_sql_file(sql_file):
    """Execute one SQL file inside container."""
    logger.info(f"Executing SQL file: {sql_file.name}")

    # Remove CSV file if it exists in container
    start = time.time()

    while time.time() - start < 30:
        sock = subprocess.run(
            [DOCKER, "exec", CONTAINER, "sh", "-c",
             "test -S /var/run/mysqld/mysqld.sock"],
            capture_output=True,
            text=True
        )
        if sock.returncode == 0 and "ready" in sock.stdout:
            logger.info("MySQL socket is ready.")
            break
    with open(sql_file, "rb") as f:
        result = subprocess.run(
            [DOCKER, "exec", "-e",
             f"MYSQL_PWD={MYSQL_PASSWORD}", "-i",
             CONTAINER,
             "mysql", "--local-infile=1",
             "-u",
             "root",
             DB],
            stdin=f,
        )

    if result.returncode != 0:
        raise RuntimeError(f"SQL execution failed for {sql_file.name}")

    logger.info(f" Finished running {sql_file.name}")


def cleanup():
    """Stop and remove Docker container."""
    logger.info("Cleaning up: Stopping Docker container...")
    run_command([DOCKER, "compose", "-f", str(COMPOSE_FILE), "down"])


def update_csv_file(file):
    """Update a CSV file with new column names."""
    columns_movies = ["title_id", "primary_title", "genres", "start_year"]
    columns_characters = ["character_name"]
    columns_directors = [
        "title_id",
        "person_id",
        "person_name",
        "job",
        "category"]
    columns_actors = ["person_id", "person_name"]

    if "movies" in file.name:
        columns = columns_movies
    elif "characters" in file.name:
        columns = columns_characters
    elif "directors" in file.name:
        columns = columns_directors
    elif "actors" in file.name:
        columns = columns_actors
    if "characters" in file.name:
        marvel_df = pd.read_csv(
            file,
            encoding='latin-1',
            header=0,
            names=columns_characters)
    else:
        marvel_df = pd.read_csv(
            file,
            sep=",",
            header=0,
            encoding="utf-8",
            engine="python",
            names=columns)

    marvel_df.to_csv(file, index=False)
    logger.debug(marvel_df.head())
    logger.debug(marvel_df.shape)
    logger.info("Returned rows: %d", len(marvel_df))

# Pipeline execution


def main():
    logger = setup_logger()
    # Start Docker container
    try:
        run_command([
            DOCKER, "compose",
            "-f", str(COMPOSE_FILE),
            "up", "-d"
        ])
        logger.info("Docker container started successfully.")
    except Exception as e:
        logger.error(f"Error starting Docker container: {e}")
        return

    # Download files from IMDB
    download_files()

    # Copy TSV files into container
    copy_tsv_to_container()

    db_setup_files = ["imdb-create-db.sql", "imdb-create-tables.sql",
                      "imdb-load-data.sql", "imdb-add-constraints.sql",
                      "imdb-add-index.sql"]

    # Execute SQL files to create DB, tables, load data, add constraints
    # and indexes
    for sql in db_setup_files:
        execute_sql_file(SQL_DIR / sql)

    #  Get SQL files
    sql_files = sorted(SQL_DIR.glob("*marvel*.sql"))
    if not sql_files:
        logger.error("No SQL files found in %s", SQL_DIR)
        raise FileNotFoundError("No SQL files found.")

    # Remove any existing CSV files in container before running queries that
    # generate new ones
    run_command([DOCKER, "exec", CONTAINER, "sh", "-c",
                "rm -f /var/lib/mysql-files/*.csv"])
    #  Execute each SQL file sequentially
    for sql_file in sql_files:
        execute_sql_file(sql_file)

    logger.info("All SQL queries executed successfully.")

    for csv in DATA_DIR.glob("*marvel*.csv"):
        update_csv_file(csv)

    cleanup()


if __name__ == "__main__":
    main()
