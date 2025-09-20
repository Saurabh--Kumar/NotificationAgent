# AI Notification Generation Agent

A scalable, multi-tenant service for generating context-aware notifications using AI.

## Project Overview

This project implements a backend service that allows B2C enterprise customers to generate timely, context-aware notifications for their end-users. The system leverages a Large Language Model (LLM) agent to craft notification suggestions based on real-time news, company campaigns, and brand identity.

## Features

- Multi-tenant architecture with data isolation
- Asynchronous task processing with Celery and Redis
- RESTful API built with FastAPI
- Integration with LLM for intelligent notification generation
- Human-in-the-loop workflow for approval
- Database persistence with PostgreSQL

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6.0+
- (Optional) Docker and Docker Compose

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd NotificationAgent
```

### 2. Set up the environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/notification_agent

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM (update with your provider's API key)
OPENAI_API_KEY=your-openai-api-key
```

### 4. Initialize the database

```bash
# Run database migrations
alembic upgrade head
```

### 5. Start the services

```bash
# Start Redis (in a separate terminal)
redis-server

# Start Celery worker (in a separate terminal)
celery -A app.tasks worker --loglevel=info

# Start the FastAPI application
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Access the interactive API documentation at `http://localhost:8000/docs`.

## Project Structure

```
.
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   ├── core/                 # Core configuration and utilities
│   ├── db/                   # Database configuration
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic models
│   └── agent/                # AI agent implementation
├── tests/                    # Test files
├── alembic/                  # Database migrations
├── .env                      # Environment variables
├── .gitignore
├── alembic.ini               # Alembic configuration
├── requirements.txt          # Project dependencies
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code with black and isort
black .
isort .

# Check code style
flake8
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head
```

## API Documentation

API documentation is available at:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## License

[Your License Here]

## Contributing

[Your contribution guidelines here]
