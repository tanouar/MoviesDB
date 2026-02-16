#!/usr/bin/env bash

set -e  # stoppe le script au premier échec

# COMPOSE_FILE="docker/docker-compose-sqlite.yml"
COMPOSE_FILE="docker/docker-compose.yml"

echo "🚀 Building Docker images and starting containers in detached mode..."
docker compose -f "$COMPOSE_FILE" up -d --build


# echo "✅ Docker Compose SQLite is up and running."
echo "✅ Docker Compose SQL is up and running."