#!/bin/bash

set -e

echo "Starting Kong AI Gateway setup..."

if [ -z "$GROQ_API_KEY" ]; then
    echo "Error: GROQ_API_KEY environment variable is not set"
    exit 1
fi

echo "Starting Docker Compose services..."
docker-compose up -d

echo "Waiting for Kong to be ready..."
timeout=300
counter=0
while ! curl -f http://localhost:8001/status >/dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "Timeout waiting for Kong to be ready"
        exit 1
    fi
    echo "Kong is not ready yet. Waiting... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

echo "Kong is ready!"

echo "Installing deck CLI tool..."
if ! command -v deck &> /dev/null; then
    echo "Installing deck..."
    curl -sL https://github.com/Kong/deck/releases/latest/download/deck_linux_amd64.tar.gz -o deck.tar.gz
    tar -xf deck.tar.gz -C /tmp
    sudo mv /tmp/deck /usr/local/bin/
    rm deck.tar.gz
fi

echo "Applying Kong configuration..."
export GROQ_API_KEY=$GROQ_API_KEY
deck sync --kong-addr http://localhost:8001 --state kong/kong.yml

echo "Creating consumers for rate limiting..."
curl -X POST http://localhost:8001/consumers \
  --data "username=support-agent" \
  --data "custom_id=support-agent-001" || true

curl -X POST http://localhost:8001/consumers/support-agent/key-auth \
  --data "key=support-agent-key-123" || true

echo "Verifying Kong setup..."
echo "Services:"
curl -s http://localhost:8001/services | jq '.data[] | {name: .name, host: .host}'

echo "Routes:"
curl -s http://localhost:8001/routes | jq '.data[] | {name: .name, paths: .paths}'

echo "Plugins:"
curl -s http://localhost:8001/plugins | jq '.data[] | {name: .name, service: .service.name}'

echo "Kong AI Gateway setup completed successfully!"
echo "Kong Proxy: http://localhost:8000"
echo "Kong Admin: http://localhost:8001"
echo "Kong Manager: http://localhost:8002"
echo "ChromaDB: http://localhost:8003"