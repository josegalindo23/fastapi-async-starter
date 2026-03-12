# FastAPI Async Starter 🚀

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

A modern FastAPI backend with async/await, SQLAlchemy 2.0, and modular architecture.
Built as a portfolio project demonstrating production-ready backend patterns.

## 🚀 Features

- ⚡ **FastAPI** with async/await support
- 🔄 **SQLAlchemy 2.0** async ORM
- 📝 **Pydantic v2** robust data validation and settings management
- 🎯 **Clean/Modular architecture** (Routers, Models, Schemas, Services, Dependencies)
- 🔐 **JWT Authentication** with access + refresh token rotation
- 🔑 **Role-based access control** (user, moderator, admin, superuser)
- 🛡️ **Password security** with bcrypt hashing and strength validation
- 🗄️ **SQLite** by default, easy to switch to PostgreSQL
- 📚 **Automatic API documentation** (Swagger UI & ReDoc)
- ✅ **Type hints** throughout for clarity and safety
- 🔒 **CORS** middleware configured for frontend integration

## 📁 Project Structure

```
fastapi-async-starter/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Centralized configuration (pydantic-settings)
│   │   └── security.py             # JWT creation/verification, bcrypt utils
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy declarative base + model imports
│   │   └── database.py             # Async engine, session factory, get_db dependency
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py                 # get_current_user, ActiveUser, AdminUser
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User ORM model
│   │   └── tokens.py               # RefreshToken ORM model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                 # User Pydantic schemas (create, update, response)
│   │   └── auth.py                 # Auth schemas (login, token, logout, reset)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py         # User CRUD business logic
│   │   └── auth_service.py         # Auth logic (login, refresh, logout, reset)
│   └── routers/
│       ├── __init__.py
│       ├── health.py               # Health check endpoint
│       ├── user.py                 # User endpoints
│       └── auth.py                 # Authentication endpoints
├── test/
│   └── test_health.py
├── dev_scripts/
├── .venv                            # Virtual Environment (not in git)
├── .env                            # Environment variables (not in git)
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
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
 Create a `.env` file in the project root (Look `.env.example` file):

```env
DATABASE_URL=sqlite+aiosqlite:///./test.db
PROJECT_NAME=FastAPI Async Starter
DEBUG=True

# Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-super-secret-key-change-in-production

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
```
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

### Public
```http
GET    /health/                         Health check
POST   /users/register                  Create account
POST   /auth/login                      Login — returns access + refresh tokens
POST   /auth/refresh                    Rotate refresh token
POST   /auth/password-reset/request     Request password reset (email)
POST   /auth/password-reset/confirm     Confirm reset with token + new password
```

### Protected (requires Bearer token)
```http
GET    /auth/me                         Get own profile
PUT    /users/me/profile                Update username / full name
PUT    /users/me/password               Change password
POST   /auth/logout                     Revoke current session
POST   /auth/logout-all                 Revoke all sessions (all devices)
```

### Admin only
```http
GET    /users/                          List all users (paginated)
GET    /users/{id}                      Get any user by ID
PUT    /users/{id}                      Update any user
DELETE /users/{id}                      Deactivate user (soft delete)
```

## 🔐 Authentication Flow

```
1. POST /users/register  →  create account
2. POST /auth/login      →  { access_token, refresh_token }
3. GET  /auth/me         →  Authorization: Bearer <access_token>
4. POST /auth/refresh    →  send refresh_token → new token pair (rotation)
5. POST /auth/logout     →  revoke refresh_token
```

**Token rotation** — every refresh request revokes the old refresh token and issues
a new one. This prevents replay attacks: a stolen refresh token becomes useless
as soon as the legitimate client uses it once.

## 🏗️ Architecture

### Layers
```
Request → Router → Service → Model → Database
                      ↓
Response ← Schema ← Service ← Model ← Database
```

### Dependency injection chain
```
get_current_user          → validates JWT, loads User from DB
  └─ get_current_active_user   → also checks is_active
       └─ get_current_admin_user    → also checks role/superuser
```

## 🗄️ Database

SQLite is used for development. Switch to PostgreSQL for production:

### Migrate to PostgreSQL

1. Install driver:

```bash
pip install asyncpg psycopg2-binary
```

2. Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

> **Note:** SQLite doesn't store timezone info in DATETIME columns.
> The codebase handles this explicitly in `RefreshToken.is_expired`
> by normalizing naive datetimes to UTC before comparison —
> so the same code works correctly on both SQLite and PostgreSQL.

### Migrate to MySQL

1. Install driver:

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
| python-jose[cryptography] | 3.5.0 | JWT encoding/decoding |
| bcrypt | 4.0.1 | Password hashing |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| python-multipart | 0.0.21 | Form data support |
| aiosqlite | 0.22.1 | Async SQLite driver |
| email-validator | 2.3.0 | Email validation |
| python-dotenv | 1.2.1 | Environment variables |

## 🗺️ Development Roadmap

### ✅ Phase 1: Core Foundation (Completed)
- [x] Project structure & configuration
- [x] Database setup with SQLAlchemy async
- [x] User CRUD operations
- [x] Password hashing with bcrypt
- [x] Automatic API documentation

### ✅ Phase 2: Authentication & Security (Completed)
- [x] JWT access + refresh token system
- [x] Refresh token rotation with DB-backed revocation
- [x] Protected routes with dependency injection
- [x] Role-based access control (user / moderator / admin / superuser)
- [x] Logout (single session + all devices)
- [x] Password reset flow with time-limited tokens

### ⚙️ Phase 3: Production Readiness (Current)
- [ ] Database migrations with Alembic
- [ ] Unit and integration tests (pytest)
- [ ] Docker configuration
- [ ] Structured logging and error handling

### 🌟 Phase 4: Advanced Features
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Rate limiting middleware
- [ ] Background tasks with Celery/RQ
- [ ] File upload support
- [ ] WebSocket real-time features

### 🚢 Phase 5: Deployment & DevOps
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Docker Compose for development
- [ ] Production deployment (Render/Railway/AWS)
- [ ] Monitoring and health checks

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License. See `LICENSE` for details.

## 👤 Author

**Your Name**
- GitHub: [@josegalindo23](https://github.com/josegalindo23)
- LinkedIn: [Jose Galindo](https://linkedin.com/in/josegalindo23)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing async web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful async ORM
- [Pydantic](https://docs.pydantic.dev/) for robust data validation

---

⭐ If this project helped you, consider giving it a star!
