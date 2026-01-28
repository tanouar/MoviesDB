#!/usr/bin/env bash

set -e

COMPOSE_FILE="docker/docker-compose-sqlite.yml"

echo "🛑 Stopping containers..."
docker stop moviesdb_sqlite
docker compose -f "$COMPOSE_FILE" down

echo "✅ Docker Compose SQLite stack stopped."
