# Customer Support Agent API Documentation

## Base URL
```
http://localhost:8080
```

## Authentication
All API requests require proper authentication headers. The system uses API key authentication for external integrations.

## Core Endpoints

### Query Processing

#### POST /api/query
Process customer query with intelligent routing and sentiment analysis.

**Request Body:**
```json
{
  "query": "string (required) - Customer query text",
  "session_id": "string (required) - Unique session identifier",
  "customer_id": "string (required) - Customer identifier"
}
```

**Response:**
```json
{
  "response": "string - AI-generated response",
  "model_used": "string - Model that processed the query",
  "sentiment_score": "float - Sentiment analysis score (-1 to 1)",
  "complexity_score": "float - Query complexity score (0 to 1)",
  "response_time_ms": "integer - Processing time in milliseconds",
  "escalated": "boolean - Whether query was escalated",
  "escalation_reason": "string - Reason for escalation (if applicable)",
  "ticket_id": "string - CRM ticket ID (if escalated)",
  "cached": "boolean - Whether response was cached"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8080/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I cannot access my account and I am very frustrated",
    "session_id": "sess_abc123",
    "customer_id": "cust_xyz789"
  }'
```

**Example Response:**
```json
{
  "response": "I understand your frustration with accessing your account. Let me help you resolve this issue immediately. To reset your account access, please follow these steps...",
  "model_used": "openai/gpt-oss-120b",
  "sentiment_score": -0.6,
  "complexity_score": 0.4,
  "response_time_ms": 1850,
  "escalated": true,
  "escalation_reason": "negative_sentiment",
  "ticket_id": "TKT-2024-001234",
  "cached": false
}
```

### Session Management

#### POST /api/session
Create a new customer support session.

**Request Body:**
```json
{
  "customer_id": "string (required) - Customer identifier",
  "session_id": "string (optional) - Custom session ID"
}
```

**Response:**
```json
{
  "session_id": "string - Generated or provided session ID",
  "customer_id": "string - Customer identifier",
  "created_at": "string - ISO timestamp",
  "status": "string - Session status (active/closed)"
}
```

#### GET /api/session/{session_id}
Retrieve session data and conversation history.

**Response:**
```json
{
  "session_id": "string",
  "customer_id": "string",
  "created_at": "string",
  "updated_at": "string",
  "status": "string",
  "messages": [
    {
      "id": "string",
      "timestamp": "string",
      "role": "string (user/assistant)",
      "content": "string",
      "metadata": {
        "model_used": "string",
        "sentiment_score": "float",
        "complexity_score": "float"
      }
    }
  ],
  "escalations": [
    {
      "ticket_id": "string",
      "reason": "string",
      "created_at": "string",
      "status": "string"
    }
  ]
}
```

#### DELETE /api/session/{session_id}
Close and archive a session.

**Response:**
```json
{
  "message": "Session closed successfully",
  "session_id": "string",
  "archived_at": "string"
}
```

### Escalation Management

#### POST /api/escalation
Create an escalation ticket for human agent intervention.

**Request Body:**
```json
{
  "session_id": "string (required) - Session identifier",
  "reason": "string (required) - Escalation reason",
  "priority": "string (required) - Priority level (low/medium/high/urgent)",
  "customer_sentiment": "float (optional) - Customer sentiment score",
  "query_complexity": "float (optional) - Query complexity score",
  "additional_context": "string (optional) - Additional context"
}
```

**Escalation Reasons:**
- `negative_sentiment` - Customer showing frustration/anger
- `high_complexity` - Query too complex for automated handling
- `repeated_failures` - Multiple failed resolution attempts
- `manual_request` - Customer explicitly requested human agent
- `policy_violation` - Query involves policy or compliance issues

**Response:**
```json
{
  "ticket_id": "string - Generated ticket ID",
  "session_id": "string",
  "priority": "string",
  "status": "string - Ticket status (open/assigned/resolved/closed)",
  "created_at": "string",
  "estimated_response_time": "string - Expected response timeframe",
  "assigned_agent": "string (optional) - Agent ID if assigned"
}
```

#### GET /api/escalation/{ticket_id}
Retrieve escalation ticket details.

**Response:**
```json
{
  "ticket_id": "string",
  "session_id": "string",
  "customer_id": "string",
  "reason": "string",
  "priority": "string",
  "status": "string",
  "created_at": "string",
  "updated_at": "string",
  "assigned_agent": "string",
  "resolution_notes": "string",
  "customer_satisfaction": "integer (1-5)"
}
```

#### PUT /api/escalation/{ticket_id}
Update escalation ticket status or assignment.

**Request Body:**
```json
{
  "status": "string (optional) - New status",
  "assigned_agent": "string (optional) - Agent ID",
  "resolution_notes": "string (optional) - Resolution details",
  "customer_satisfaction": "integer (optional) - Satisfaction rating"
}
```

### Analytics and Metrics

#### GET /api/metrics
Retrieve system performance metrics.

**Query Parameters:**
- `timeframe` - Time period (hour/day/week/month)
- `start_date` - Start date (ISO format)
- `end_date` - End date (ISO format)

**Response:**
```json
{
  "timeframe": "string",
  "total_queries": "integer",
  "avg_response_time_ms": "float",
  "model_usage": {
    "llama-3.3-70b-versatile": "integer",
    "openai/gpt-oss-120b": "integer",
    "llama-3.1-8b-instant": "integer"
  },
  "sentiment_distribution": {
    "positive": "integer",
    "neutral": "integer",
    "negative": "integer"
  },
  "escalation_rate": "float",
  "cache_hit_rate": "float",
  "cost_metrics": {
    "total_cost": "float",
    "cost_per_query": "float",
    "cost_by_model": {
      "llama-3.3-70b-versatile": "float",
      "openai/gpt-oss-120b": "float"
    }
  }
}
```

#### GET /api/metrics/session/{session_id}
Get metrics for a specific session.

**Response:**
```json
{
  "session_id": "string",
  "total_messages": "integer",
  "avg_sentiment": "float",
  "avg_complexity": "float",
  "models_used": ["string"],
  "total_response_time_ms": "integer",
  "escalated": "boolean",
  "satisfaction_score": "float"
}
```

### Health and Status

#### GET /health
System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "string",
  "version": "string",
  "services": {
    "kong_gateway": "healthy",
    "groq_api": "healthy",
    "chromadb": "healthy",
    "crm_system": "healthy"
  },
  "uptime_seconds": "integer"
}
```

#### GET /api/status
Detailed system status information.

**Response:**
```json
{
  "system_status": "operational",
  "active_sessions": "integer",
  "queue_length": "integer",
  "avg_response_time_ms": "float",
  "error_rate": "float",
  "last_deployment": "string",
  "maintenance_window": "string (optional)"
}
```

## Error Responses

All endpoints return standardized error responses with appropriate HTTP status codes.

### Error Format
```json
{
  "error": true,
  "error_type": "string - Error category",
  "message": "string - Human-readable error message",
  "details": "string (optional) - Additional error details",
  "timestamp": "string - ISO timestamp",
  "request_id": "string - Unique request identifier"
}
```

### Error Types
- `VALIDATION_ERROR` (400) - Invalid request format or parameters
- `AUTHENTICATION_ERROR` (401) - Missing or invalid authentication
- `AUTHORIZATION_ERROR` (403) - Insufficient permissions
- `NOT_FOUND_ERROR` (404) - Resource not found
- `RATE_LIMIT_ERROR` (429) - Rate limit exceeded
- `KONG_GATEWAY_ERROR` (502) - Kong Gateway issues
- `LLM_API_ERROR` (503) - AI model API issues
- `DATABASE_ERROR` (503) - Database connectivity issues
- `TIMEOUT_ERROR` (504) - Request timeout
- `INTERNAL_ERROR` (500) - Unexpected server error

### Example Error Response
```json
{
  "error": true,
  "error_type": "VALIDATION_ERROR",
  "message": "Missing required field: customer_id",
  "details": "The customer_id field is required for all query requests",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123def456"
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability.

### Limits
- **Query Endpoint**: 60 requests per minute per IP
- **Session Endpoints**: 100 requests per minute per IP
- **Metrics Endpoints**: 30 requests per minute per IP

### Rate Limit Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248600
```

## Webhooks

The system supports webhooks for real-time notifications.

### Escalation Webhook
Triggered when a new escalation is created.

**Payload:**
```json
{
  "event": "escalation.created",
  "timestamp": "string",
  "data": {
    "ticket_id": "string",
    "session_id": "string",
    "customer_id": "string",
    "priority": "string",
    "reason": "string"
  }
}
```

### Session Webhook
Triggered when a session is closed.

**Payload:**
```json
{
  "event": "session.closed",
  "timestamp": "string",
  "data": {
    "session_id": "string",
    "customer_id": "string",
    "duration_minutes": "integer",
    "message_count": "integer",
    "escalated": "boolean"
  }
}
```

## SDK Examples

### Python SDK
```python
import requests

class CustomerSupportClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        
    def query(self, text, session_id, customer_id):
        response = requests.post(f"{self.base_url}/api/query", json={
            "query": text,
            "session_id": session_id,
            "customer_id": customer_id
        })
        return response.json()
    
    def create_escalation(self, session_id, reason, priority="medium"):
        response = requests.post(f"{self.base_url}/api/escalation", json={
            "session_id": session_id,
            "reason": reason,
            "priority": priority
        })
        return response.json()

# Usage
client = CustomerSupportClient()
result = client.query("How do I reset my password?", "sess_123", "cust_456")
print(result["response"])
```

### JavaScript SDK
```javascript
class CustomerSupportClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }
    
    async query(text, sessionId, customerId) {
        const response = await fetch(`${this.baseUrl}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: text,
                session_id: sessionId,
                customer_id: customerId
            })
        });
        return response.json();
    }
    
    async createEscalation(sessionId, reason, priority = 'medium') {
        const response = await fetch(`${this.baseUrl}/api/escalation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                reason: reason,
                priority: priority
            })
        });
        return response.json();
    }
}

// Usage
const client = new CustomerSupportClient();
const result = await client.query("How do I reset my password?", "sess_123", "cust_456");
console.log(result.response);
```

## Testing

### Test Endpoints
Use these endpoints for testing and development:

#### POST /api/test/query
Simulate query processing without calling external APIs.

#### POST /api/test/escalation
Create test escalation tickets.

#### GET /api/test/metrics
Generate sample metrics data.

### Example Test Scenarios
```bash
# Test simple query
curl -X POST "http://localhost:8080/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your hours?", "session_id": "test_1", "customer_id": "test_user"}'

# Test complex query
curl -X POST "http://localhost:8080/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "I need help with integrating your API with our enterprise system using OAuth 2.0 and handling webhook callbacks", "session_id": "test_2", "customer_id": "test_user"}'

# Test negative sentiment
curl -X POST "http://localhost:8080/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "This is terrible! Nothing works and I am extremely frustrated!", "session_id": "test_3", "customer_id": "test_user"}'
```
