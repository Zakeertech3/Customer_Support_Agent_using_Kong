# Customer Support Agent

Intelligent customer support system powered by Kong AI Gateway with advanced query routing, sentiment analysis, and escalation management.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI        │    │   Kong Gateway  │
│   Frontend      │───▶│   Backend        │───▶│   AI Router     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       ▼
         │                        │              ┌─────────────────┐
         │                        │              │   Groq Models   │
         │                        │              │                 │
         │                        │              │ • llama-3.3-70b │
         │                        │              │ • gpt-oss-120b  │
         │                        │              │ • llama-3.1-8b  │
         │                        │              └─────────────────┘
         │                        │
         │                        ▼
         │               ┌─────────────────┐
         │               │   ChromaDB      │
         │               │   Vector Store  │
         │               └─────────────────┘
         │
         ▼
┌─────────────────┐
│   CRM System    │
│   Escalations   │
└─────────────────┘
```

## Key Features

### Intelligent Query Routing
- Complexity analysis using embeddings
- Automatic model selection based on query type
- Simple queries → llama-3.3-70b-versatile (cost-effective)
- Complex queries → openai/gpt-oss-120b (high-performance)

### Real-time Sentiment Analysis
- Customer emotion detection
- Automatic escalation for frustrated customers
- Sentiment scoring and tracking

### Escalation Management
- Automatic escalation triggers
- CRM ticket creation
- Human agent handoff workflow
- Priority-based routing

### Performance Monitoring
- Real-time metrics dashboard
- Response time tracking
- Model usage analytics
- Cost optimization insights

## System Requirements

### Dependencies
- Python 3.8+
- Streamlit 1.28+
- FastAPI 0.104+
- Kong Gateway 3.0+
- ChromaDB 0.4+
- Groq API access

### Hardware Requirements
- RAM: 4GB minimum, 8GB recommended
- CPU: 2 cores minimum, 4 cores recommended
- Storage: 2GB free space
- Network: Stable internet connection for API calls

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd cus_chat_sup
```

### 2. Create Virtual Environment
```bash
python -m venv ccup
source ccup/bin/activate  # Linux/Mac
ccup\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
KONG_ADMIN_URL=http://localhost:8001
KONG_GATEWAY_URL=http://localhost:8000
CHROMA_HOST=localhost
CHROMA_PORT=8000
CRM_API_URL=http://localhost:9000
LOG_LEVEL=INFO
```

### 5. Kong Gateway Setup
```bash
# Install Kong
curl -Lo kong-3.4.2.amd64.deb "https://packages.konghq.com/public/kong-deb/deb/ubuntu/pool/jammy/main/k/ko/kong_3.4.2_amd64.deb"
sudo dpkg -i kong-3.4.2.amd64.deb

# Configure Kong
kong config init
kong start
```

### 6. ChromaDB Setup
```bash
# Install ChromaDB
pip install chromadb

# Start ChromaDB server
chroma run --host localhost --port 8000
```

## Running the Application

### 1. Start Backend Services
```bash
# Terminal 1: Start Kong Gateway
kong start

# Terminal 2: Start ChromaDB
chroma run --host localhost --port 8000

# Terminal 3: Start FastAPI Backend
python main.py
```

### 2. Start Frontend
```bash
# Terminal 4: Start Streamlit
streamlit run streamlit_app.py
```

### 3. Access Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8080
- Kong Admin: http://localhost:8001
- ChromaDB: http://localhost:8000

## Configuration

### Kong Gateway Configuration
The system uses Kong for intelligent routing between different LLM models based on query complexity.

#### Service Definitions
```yaml
services:
  - name: groq-llama-70b
    url: https://api.groq.com/openai/v1
    plugins:
      - name: request-transformer
        config:
          add:
            headers:
              - "Authorization: Bearer ${GROQ_API_KEY}"
  
  - name: groq-gpt-120b
    url: https://api.groq.com/openai/v1
    plugins:
      - name: request-transformer
        config:
          add:
            headers:
              - "Authorization: Bearer ${GROQ_API_KEY}"
```

#### Routing Rules
```yaml
routes:
  - name: simple-queries
    service: groq-llama-70b
    paths: ["/api/query/simple"]
    
  - name: complex-queries
    service: groq-gpt-120b
    paths: ["/api/query/complex"]
```

### Model Configuration
```python
MODEL_CONFIG = {
    "simple_threshold": 0.3,
    "complex_threshold": 0.7,
    "sentiment_escalation_threshold": -0.5,
    "models": {
        "simple": "llama-3.3-70b-versatile",
        "complex": "openai/gpt-oss-120b",
        "fallback": "llama-3.1-8b-instant"
    }
}
```

## API Documentation

### Core Endpoints

#### POST /api/query
Process customer query with intelligent routing
```json
{
  "query": "How do I reset my password?",
  "session_id": "sess_12345",
  "customer_id": "cust_67890"
}
```

Response:
```json
{
  "response": "To reset your password...",
  "model_used": "llama-3.3-70b-versatile",
  "sentiment_score": 0.1,
  "complexity_score": 0.2,
  "response_time_ms": 1250,
  "escalated": false
}
```

#### POST /api/escalation
Create escalation ticket
```json
{
  "session_id": "sess_12345",
  "reason": "high_complexity",
  "priority": "high",
  "customer_sentiment": -0.8
}
```

#### GET /api/session/{session_id}
Retrieve session data and conversation history

#### GET /api/metrics
Get system performance metrics

### Error Handling
All endpoints return standardized error responses:
```json
{
  "error": true,
  "error_type": "VALIDATION_ERROR",
  "message": "Invalid request format",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Usage Examples

### Basic Query Processing
```python
import requests

response = requests.post("http://localhost:8080/api/query", json={
    "query": "What are your business hours?",
    "session_id": "demo_session",
    "customer_id": "demo_customer"
})

result = response.json()
print(f"Response: {result['response']}")
print(f"Model: {result['model_used']}")
print(f"Sentiment: {result['sentiment_score']}")
```

### Escalation Workflow
```python
# Check if escalation is needed
if result['sentiment_score'] < -0.5 or result['complexity_score'] > 0.8:
    escalation = requests.post("http://localhost:8080/api/escalation", json={
        "session_id": result['session_id'],
        "reason": "negative_sentiment" if result['sentiment_score'] < -0.5 else "high_complexity",
        "priority": "high"
    })
```

## Performance Optimization

### Caching Strategy
- Response caching for common queries
- Session state persistence
- Model result caching

### Load Balancing
- Kong Gateway handles load distribution
- Multiple Groq API endpoints
- Failover mechanisms

### Monitoring
- Real-time performance metrics
- Error rate tracking
- Cost optimization alerts

## Troubleshooting

### Common Issues

#### Backend Connection Errors
```
Error: HTTPConnectionPool(host='localhost', port=8080): Read timed out
```
Solution: Ensure FastAPI backend is running on port 8080

#### Kong Gateway Issues
```
Error: Kong Gateway not responding
```
Solution: Check Kong status and restart if needed
```bash
kong health
kong restart
```

#### Model API Errors
```
Error: Groq API rate limit exceeded
```
Solution: Check API key and rate limits, implement backoff strategy

### Logs Location
- Application logs: `logs/app.log`
- Kong logs: `/usr/local/kong/logs/`
- ChromaDB logs: `chroma.log`

## Development

### Project Structure
```
cus_chat_sup/
├── app/
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic
│   └── models/          # Data models
├── components/          # Reusable components
├── config/             # Configuration files
├── scripts/            # Deployment scripts
├── tests/              # Test suites
├── main.py             # FastAPI application
├── streamlit_app.py    # Frontend application
└── requirements.txt    # Dependencies
```

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run performance tests
python -m pytest tests/performance/
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## Security Considerations

### API Security
- API key authentication
- Rate limiting
- Input validation
- CORS configuration

### Data Privacy
- No sensitive data logging
- Session data encryption
- GDPR compliance ready

## Deployment

### Production Deployment
```bash
# Build Docker containers
docker-compose build

# Deploy services
docker-compose up -d

# Verify deployment
curl http://localhost:8080/health
```

### Environment Variables
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
GROQ_API_KEY=prod_key_here
```

## Support

### Documentation
- API Reference: `/docs` endpoint
- Architecture Diagrams: `docs/architecture/`
- Deployment Guide: `docs/deployment/`

### Contact
- Technical Issues: Create GitHub issue
- Feature Requests: Submit enhancement request
- Security Issues: Contact security team

## License

This project is licensed under the MIT License - see LICENSE file for details.
