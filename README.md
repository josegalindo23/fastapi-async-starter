# FastAPI Async Starter 🚀

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

A modern FastAPI backend with async/await, SQLAlchemy 2.0, and modular architecture. 

## 🚀 Features

- ⚡ **FastAPI** with async/await support
- 🔄 **SQLAlchemy 2.0** async ORM
- 📝 **Pydantic v2** Robust Data Validation and Settings Management
- 🎯 **Clean/Modular architecture** (Routers, Models, Schemas, Services)
- 🔐 **Password hashing** with bcrypt via Passlib
- 🗄️ **SQLite database** (easy to switch to PostgreSQL)
- 📚 **Automatic API documentation** (Swagger UI & ReDoc)
- ✅ **Type Hints**: Code types for better clarity and error checking  
- 🔒 **CORS Configuration**: Middleware setup for cross-origin requests, essential for frontend-backend communication

## 📁 Project Structure

```
fastapi-async-starter/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Centralized configuration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py            # SQLAlchemy declarative base
│   │   └── database.py        # DB engine and async sessions
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py            # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py            # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py    # Business Logic
│   └── routers/
│       ├── __init__.py
│       ├── health.py          # Health check endpoint
│       └── users.py           # User endpoints 
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template 
├── .gitignore
├── requirements.txt
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip or poetry

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/josegalindo23/fastapi-async-starter.git
cd fastapi-async-starter
```

2. **Create virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
 Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite+aiosqlite:///./test.db
PROJECT_NAME=FastAPI Async Starter
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production
```
5. **Run the application**

```bash
uvicorn app.main:app --reload --port 8000
```

The application will be available at:
- 🌐 API: http://localhost:8000
- 📖 Documentation (Swagger): http://localhost:8000/docs
- 📘 Documentation (ReDoc): http://localhost:8000/redoc

## 🔧 API Endpoints

```http
GET    /health/          Health check
POST   /users/           Create user  
GET    /users/           List users
GET    /users/{id}       Get user by ID
```

### Application Layers

1. **Routers** (`app/routers/`) - HTTP endpoints and request validation
2. **Services** (`app/services/`) - Business logic and rules
3. **Models** (`app/models/`) - Database table definitions
4. **Schemas** (`app/schemas/`) - Data validation and serialization

### Data Flow

```
Request → Router → Service → Model → Database
                      ↓
Response ← Schema ← Service ← Model ← Database
```

## 🗄️ Database

### Migrate to PostgreSQL

1. Install dependencies:

```bash
pip install asyncpg psycopg2-binary
```

2. Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

### Migrate to MySQL

1. Install dependencies:

```bash
pip install aiomysql
```

2. Update `.env`:

```env
DATABASE_URL=mysql+aiomysql://user:password@localhost/dbname
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📦 Main Dependencies

| Package | Version | Purpose |
|---------|---------|-----------|
| fastapi | 0.128.0 | Web framework |
| uvicorn | 0.40.0 | ASGI server |
| sqlalchemy | 2.0.45 | Async ORM |
| pydantic | 2.12.5 | Data validation |
| pydantic-settings | 2.4.0 | Settings management |
| bcrypt | 4.0.1 | Password hashing |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| aiosqlite | 0.22.1 | Async SQLite driver |
| email-validator | 2.3.0 | Email validation |
| python-dotenv | 1.2.1 | Environment variables |

### Environment Variables in Production (Example)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=generate-a-strong-random-key
DEBUG=False
```

## 🗺️ Development Roadmap

### ✅ Phase 1: Core Foundation (Completed)
- [x] Project structure & configuration
- [x] Database setup with SQLAlchemy async
- [x] User CRUD operations
- [x] Password hashing with bcrypt
- [x] Automatic API documentation

### 🚀 Phase 2: Authentication & Security (Current)
- [ ] JWT authentication endpoints
- [ ] Protected routes with dependencies
- [ ] Refresh token mechanism
- [ ] Password reset functionality

### ⚙️ Phase 3: Production Readiness
- [ ] Database migrations with Alembic
- [ ] Unit and integration tests (pytest)
- [ ] Docker configuration
- [ ] Environment-based configuration
- [ ] Logging and error handling improvements

### 🌟 Phase 4: Advanced Features
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Rate limiting middleware
- [ ] Background tasks with Celery/RQ
- [ ] File upload support
- [ ] WebSocket implementation for real-time features

### 🚢 Phase 5: Deployment & DevOps
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Docker Compose for development
- [ ] Production deployment (Render/Railway/AWS)
- [ ] Monitoring and health checks
- [ ] API documentation deployment

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 👤 Author

**Your Name**
- GitHub: [@josegalindo23](https://github.com/josegalindo23)
- LinkedIn: [Jose Galindo](https://linkedin.com/in/josegalindo23)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing async web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful async ORM
- [Pydantic](https://docs.pydantic.dev/) for robust data validation
- The Python community for endless inspiration

---

⭐ If this project helped you, consider giving it a star on GitHub!