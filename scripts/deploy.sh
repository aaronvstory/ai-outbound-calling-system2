#!/bin/bash
# Deployment script for AI Calling System

set -e

echo "🚀 Deploying AI Calling System..."

# Configuration
APP_NAME="ai-calling-system"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-app"

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t $DOCKER_IMAGE --target production .

# Stop existing container if running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "⏹️ Stopping existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run new container
echo "▶️ Starting new container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 5000:5000 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    --env-file .env \
    $DOCKER_IMAGE

# Wait for container to be ready
echo "⏳ Waiting for application to start..."
sleep 10

# Health check
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! Application is running at http://localhost:5000"
else
    echo "❌ Deployment failed! Check container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Show container status
echo "📊 Container status:"
docker ps -f name=$CONTAINER_NAME