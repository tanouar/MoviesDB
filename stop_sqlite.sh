#!/usr/bin/env bash

set -e

COMPOSE_FILE="docker/docker-compose-sqlite.yml"
CONTAINER_NAME="moviesdb_sqlite"

echo "🛑 Stopping containers..."

docker stop "$CONTAINER_NAME" 
docker compose -f "$COMPOSE_FILE" down

echo "✅ Docker Compose SQLite stack stopped."
