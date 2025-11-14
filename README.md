# Dynamic LLM Routing System

An intelligent routing system that dynamically selects the best Large Language Model (LLM) for each query based on complexity, cost, and performance ratings. The system includes a smart rating mechanism, user management, and a modern React frontend.

## 🌟 Features

### Core Features
- **Dynamic Model Selection**: Automatically routes queries to the most suitable LLM based on complexity classification
- **Multi-Tier Architecture**: Three-tier system (Simple, Medium, Advanced) for optimal cost-performance balance
- **Real-time Rating System**: Users can rate model responses with likes, dislikes, and star ratings
- **Semantic Caching**: Intelligent caching system to reduce API calls and improve response times
- **Fallback Chain**: Automatic fallback to alternative models if primary model fails
- **User API Key Support**: Users can bring their own API keys or use system-provided ones

### Frontend Features
- **Modern React UI**: Clean, responsive interface built with React and Tailwind CSS
- **Real-time Dashboard**: Monitor query statistics, costs, and performance metrics
- **Interactive Chatbot**: Test models with real-time feedback and rating
- **Batch Processing**: Process multiple queries simultaneously
- **Leaderboard System**: View model rankings based on user ratings
- **User Management**: Register, login, and manage API keys

### Backend Features
- **FastAPI Backend**: High-performance async API framework
- **SQLAlchemy ORM**: Robust database management with SQLite/PostgreSQL support
- **JWT Authentication**: Secure user authentication and authorization
- **Dynamic Configuration**: Hot-reload model configurations without restart
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │   Database      │
│                 │    │   Backend       │    │   (SQLite/PG)   │
│ • Dashboard     │◄──►│                 │◄──►│                 │
│ • Chatbot       │    │ • Router        │    │ • Users         │
│ • Settings      │    │ • Rating API    │    │ • Models        │
│ • Leaderboard   │    │ • Auth          │    │ • Ratings       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   LLM Models    │
                       │                 │
                       │ • OpenAI        │
                       │ • Anthropic     │
                       │ • OpenRouter    │
                       │ • Custom APIs   │
                       └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Git

## 🚀 Quick Start

Get the Dynamic LLM Router running in minutes with these simple steps:

### 1. Clone the Repository
```bash
git clone https://github.com/HagAli22/LLM_Dynamic_routing.git
cd LLM_Dynamic_routing
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python migrate_rating_system.py

# Start backend server
python run_backend.py
```

### 3. Frontend Setup
```bash
# Open a new terminal window
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 🎉 You're all set!
The application is now running with:
- ✅ Intelligent LLM routing system
- ✅ Real-time model rating and feedback
- ✅ Modern React frontend
- ✅ User authentication and API key management
- ✅ Analytics dashboard and monitoring

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./llm_router.db

# Application Settings
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Model Configuration
DEFAULT_TIER=tier1
MAX_RETRIES_PER_MODEL=3
SEMANTIC_CACHE_TTL=3600
```

### Model Configuration
Models are configured in `config.py` with the following structure:

```python
MODELS_CONFIG = {
    "tier1": [
        ["gpt-3.5-turbo", "openai/gpt-3.5-turbo"],
        ["claude-haiku", "anthropic/claude-3-haiku-20240307"],
    ],
    "tier2": [
        ["gpt-4", "openai/gpt-4"],
        ["claude-sonnet", "anthropic/claude-3-sonnet-20240229"],
    ],
    "tier3": [
        ["gpt-4-turbo", "openai/gpt-4-turbo-preview"],
        ["claude-opus", "anthropic/claude-3-opus-20240229"],
    ]
}
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user info

### Routing
- `POST /api/route` - Route a query to the best model
- `GET /api/classify` - Classify query complexity

### Rating System
- `POST /api/rating/feedback` - Submit model feedback
- `GET /api/rating/leaderboard/{tier}` - Get model rankings
- `GET /api/rating/stats/{model_id}` - Get model statistics

### User Management
- `GET /api/user/stats` - Get user statistics
- `POST /api/user/api-keys` - Add API key
- `DELETE /api/user/api-keys/{key_id}` - Delete API key

## 🎯 Usage Examples

### Basic Query Routing
```python
import requests

# Login to get token
response = requests.post("http://localhost:8000/api/auth/login", 
    data={"username": "admin", "password": "admin"})
token = response.json()["access_token"]

# Route a query
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/api/route",
    json={"query": "What is machine learning?"},
    headers=headers)

print(response.json()["response"])
```

### Submit Model Rating
```python
# Submit feedback for a model
feedback_data = {
    "query_id": 123,
    "model_identifier": "openai/gpt-4",
    "feedback_type": "like",
    "comment": "Great response!"
}

response = requests.post("http://localhost:8000/api/rating/feedback",
    json=feedback_data,
    headers=headers)
```

## 🏆 Rating System

The system uses a sophisticated rating mechanism:

### Rating Types
- **Like**: +5 points to model score
- **Dislike**: -5 points to model score  
- **Star**: +10 points to model score

### Ranking Algorithm
1. **Base Score**: Initial score of 100 points
2. **User Feedback**: Points added/subtracted based on ratings
3. **Success Rate**: Models with higher success rates get priority
4. **Cost Efficiency**: Cheaper models may get bonus points for good performance

### Leaderboard Tiers
- **Tier 1 (Simple)**: Fast, cost-effective models for basic queries
- **Tier 2 (Medium)**: Balanced models for moderate complexity
- **Tier 3 (Advanced)**: Powerful models for complex tasks

## 🔧 Development

### Backend Development
```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/

# Check code style
flake8 .
black .
```

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Check code style
npm run lint
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📝 Testing

### Backend Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_rating_system.py

# Run with coverage
python -m pytest --cov=.
```

### Frontend Tests
```bash
cd frontend

# Run unit tests
npm test

# Run integration tests
npm run test:e2e
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Setup
1. **Backend**:
   - Use PostgreSQL instead of SQLite
   - Set up reverse proxy (nginx)
   - Configure SSL certificates
   - Set up monitoring and logging

2. **Frontend**:
   - Build optimized production bundle
   - Configure CDN for static assets
   - Set up environment variables for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/React
- Write comprehensive tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models  
- OpenRouter for model aggregation
- FastAPI for the backend framework
- React for the frontend framework

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the [documentation](docs/)
- Review existing [discussions](https://github.com/HagAli22/LLM_Dynamic_routing/discussions)

## 🔮 Roadmap

- [ ] Support for more LLM providers
- [ ] Advanced analytics dashboard
- [ ] Custom model fine-tuning integration
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Enterprise features (SSO, RBAC)
- [ ] Model performance monitoring
- [ ] Cost optimization algorithms

---

**Built with ❤️ by the Dynamic LLM Router Team**
