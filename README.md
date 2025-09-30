# Customer Support Agent

Intelligent customer support system powered by Kong AI Gateway with advanced query routing, sentiment analysis, and escalation management.

## 🖼️ System Demonstration

### Interface Overview
![Customer Support Agent Interface](https://github.com/user-attachments/assets/5371ae52-e08d-4634-b8f4-3087ecfa4afb)
*Clean, professional customer support interface powered by Kong AI Gateway*

### Simple Query Processing
![Simple Query Example](https://github.com/user-attachments/assets/f4319534-1bc9-4061-9802-837247832ff8)
*Warranty inquiry routed to cost-effective llama-3.3-70b model with instant response*

### Complex Query Handling
![Complex Query Processing](https://github.com/user-attachments/assets/7f20b543-059e-4ef6-be1e-6e35c288c8d3)
*Multi-symptom troubleshooting routed to high-performance gpt-oss-120b model*

![Complex Query Response](https://github.com/user-attachments/assets/09680845-8fa2-45ba-b466-9661e5a64708)
*Detailed diagnostic steps and solution provided for complex appliance issues*

![Query Processing Stages](https://github.com/user-attachments/assets/c7b3de48-db66-497f-bcd5-c07a0c3963f5)
*Real-time processing stages: analyzing → routing → processing → sentiment → complete*

### Sentiment Analysis & Escalation
![Negative Sentiment Detection](https://github.com/user-attachments/assets/cc1ccb23-141f-4ae8-9a32-7e7fe0281e02)
*Automatic detection of customer frustration with sentiment score -0.64*

![Escalation Management](https://github.com/user-attachments/assets/4c3c6005-11a4-42c9-b68c-96cef3b7c200)
*Seamless escalation to human agents with empathetic response and ticket creation*

### Performance Optimization
![Caching System](<img width="908" height="753" alt="Image" src="https://github.com/user-attachments/assets/bcb47aed-57d0-4089-bbbe-47f2c85e73c8" />)
*Intelligent caching system for improved response times and cost optimization*

### Analytics Dashboard
![Session Analytics](https://github.com/user-attachments/assets/6408f495-f63c-4f97-b5d2-3bd80fb50664)
*Real-time session metrics and performance tracking*

![Cost Analysis](https://github.com/user-attachments/assets/68d94cc2-13e1-46f0-a717-a8f5f09dd0f4)
*Comprehensive cost analysis with token usage and model distribution*

![Performance Metrics](https://github.com/user-attachments/assets/6d9aed36-e0c0-4250-a436-379c5f15e229)
*Response time analysis and model performance benchmarks*

![System Statistics](https://github.com/user-attachments/assets/54b82a88-be90-4178-b100-33439184b456)
*Complete system statistics including sentiment analysis and complexity distribution*

## 🎯 Key Demonstration Points

- **Intelligent Routing**: Simple queries → cost-effective models, complex queries → high-performance models
- **Sentiment Analysis**: Real-time emotion detection with automatic escalation triggers
- **Performance Monitoring**: Comprehensive analytics for response times, costs, and customer satisfaction
- **Seamless Experience**: Professional interface with clear processing stages and instant responses

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
git clone https://github.com/Zakeertech3/Customer_Support_Agent_using_Kong.git
```

### 2. Create Virtual Environment
```bash
python -m venv venv

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
