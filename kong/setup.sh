#!/bin/bash

set -e

echo "Waiting for Kong to be ready..."
until curl -f http://localhost:8001/status; do
    echo "Kong is not ready yet. Waiting..."
    sleep 5
done

echo "Kong is ready. Applying configuration..."

export GROQ_API_KEY=${GROQ_API_KEY}

deck sync --kong-addr http://localhost:8001 --state kong/kong.yml

echo "Kong configuration applied successfully!"

echo "Creating consumers for rate limiting..."
curl -X POST http://localhost:8001/consumers \
  --data "username=support-agent" \
  --data "custom_id=support-agent-001"

curl -X POST http://localhost:8001/consumers/support-agent/key-auth \
  --data "key=support-agent-key-123"

echo "Kong setup completed successfully!"