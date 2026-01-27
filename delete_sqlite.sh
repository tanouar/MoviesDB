#!/usr/bin/env bash

set -e

echo "⚠️  WARNING: This will STOP all running Docker containers"
echo "⚠️  and DELETE:"
echo "   - stopped containers"
echo "   - unused images"
echo "   - unused networks"
echo "   - unused volumes (⚠️ DATA LOSS)"


read -p "Type YES to confirm, anything else to cancel: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
  echo "❌ Aborted. Nothing was changed."
  exit 0
fi

docker stop $(docker ps -q)
docker system prune -a --volumes -f


echo "✅ Docker system cleaned up."