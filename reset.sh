#!/bin/bash

echo "🛑 Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null

echo "🗑️ Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null

echo "🖼️ Removing all images..."
# The -f forces removal even if the image is tagged
docker rmi -f $(docker images -q) 2>/dev/null

echo "🧹 Final system deep clean..."
docker system prune -a --volumes -f

echo "✅ Docker environment is now empty."

docker compose up -d