# Kong AI Gateway Setup Guide

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Groq API Key** - Get from https://console.groq.com/
3. **deck CLI** (optional) - Kong configuration management tool

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your API key:

```bash
cp .env.example .env
```

Edit `.env` and set your `GROQ_API_KEY`:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 2. Start Kong AI Gateway

**Windows:**

```cmd
scripts\start-kong.bat
```

**Linux/Mac:**

```bash
chmod +x scripts/start-kong.sh
./scripts/start-kong.sh
```

### 3. Validate Setup

```bash
python scripts/validate-kong.py
```

## Services Overview

| Service      | Port | Description                          |
| ------------ | ---- | ------------------------------------ |
| Kong Proxy   | 8000 | Main API Gateway endpoint            |
| Kong Admin   | 8001 | Admin API for configuration          |
| Kong Manager | 8002 | Web UI for Kong management           |
| ChromaDB     | 8003 | Vector database for semantic caching |
| PostgreSQL   | 5432 | Kong's database (internal)           |

## AI Routes Configuration

### Model Routing

- **Simple Queries** → `POST /ai/simple` → `llama-3.3-70b-versatile`
- **Complex Queries** → `POST /ai/complex` → `openai/gpt-oss-120b`
- **Fallback** → `POST /ai/fallback` → `llama-3.1-8b-instant`

### Plugin Configuration

#### AI Proxy Advanced

- **Purpose**: Route requests to appropriate Groq models
- **Features**: Model selection, request transformation, authentication
- **Configuration**: Per-service model mapping with weights

#### AI Semantic Cache

- **Purpose**: Cache similar queries using vector similarity
- **Backend**: ChromaDB vector database
- **Threshold**: 85% similarity for cache hits
- **TTL**: 1 hour (3600 seconds)

#### AI Prompt Guard

- **Purpose**: Content moderation and safety filtering
- **Features**: Allow/deny patterns, request size limits
- **Patterns**: Blocks malicious content, allows support queries

#### AI Rate Limiting Advanced

- **Purpose**: Token-based rate limiting per consumer
- **Limits**:
  - Simple: 100 requests/minute
  - Complex: 50 requests/minute
  - Fallback: 200 requests/minute

## Testing the Setup

### 1. Health Check

```bash
curl http://localhost:8001/status
```

### 2. Test Simple Query

```bash
curl -X POST http://localhost:8000/ai/simple \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, how can you help me?"}],
    "max_tokens": 100
  }'
```

### 3. Test Complex Query

```bash
curl -X POST http://localhost:8000/ai/complex \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Explain the architecture of microservices with Kong API Gateway"}],
    "max_tokens": 500
  }'
```

## Troubleshooting

### Kong Not Starting

1. Check Docker is running: `docker ps`
2. Check ports are available: `netstat -an | findstr :8000`
3. Check logs: `docker-compose logs kong`

### Plugin Configuration Issues

1. Verify plugins are loaded: `curl http://localhost:8001/plugins`
2. Check plugin configuration: `deck dump --kong-addr http://localhost:8001`
3. Validate configuration: `deck validate --state kong/kong.yml`

### ChromaDB Connection Issues

1. Check ChromaDB is running: `curl http://localhost:8003/api/v1/heartbeat`
2. Check Docker logs: `docker-compose logs chromadb`
3. Verify network connectivity: `docker network ls`

### Groq API Issues

1. Verify API key is set: `echo $GROQ_API_KEY`
2. Test direct API access:
   ```bash
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

## Configuration Files

- `docker-compose.yml` - Docker services definition
- `kong/kong.yml` - Kong declarative configuration
- `scripts/start-kong.sh` - Setup automation script
- `scripts/validate-kong.py` - Validation and testing

## Advanced Configuration

### Custom Plugin Configuration

Edit `kong/kong.yml` to modify plugin settings:

```yaml
plugins:
  - name: ai-semantic-cache
    service: groq-llama-simple
    config:
      similarity_threshold: 0.90 # Increase for stricter matching
      ttl: 7200 # 2 hours cache
      max_cache_size: 2000 # More cache entries
```

### Adding New Routes

1. Add service definition in `kong/kong.yml`
2. Create corresponding route
3. Apply plugins as needed
4. Sync configuration: `deck sync --kong-addr http://localhost:8001 --state kong/kong.yml`

## Monitoring and Observability

### Kong Manager UI

Access Kong Manager at http://localhost:8002 to:

- View service topology
- Monitor plugin performance
- Analyze request patterns
- Configure rate limiting

### API Analytics

Use Kong Admin API for programmatic monitoring:

```bash
# Get plugin statistics
curl http://localhost:8001/plugins

# Get service metrics
curl http://localhost:8001/services

# Get route analytics
curl http://localhost:8001/routes
```

## Production Considerations

1. **Security**: Use proper authentication and HTTPS
2. **Scaling**: Configure Kong in cluster mode
3. **Monitoring**: Integrate with Prometheus/Grafana
4. **Backup**: Regular database backups
5. **Rate Limiting**: Adjust limits based on usage patterns
