# AI Notification Generation Agent

A scalable, multi-tenant service for generating context-aware notifications using AI.

## Project Overview

This project implements a backend service that allows B2C enterprise customers to generate timely, context-aware notifications for their end-users. The system leverages a Large Language Model (LLM) agent to craft notification suggestions based on real-time news, company campaigns, and brand identity.

## Features

- Multi-tenant architecture with data isolation
- Asynchronous task processing using a background thread pool
- RESTful API built with FastAPI
- Integration with LLM for intelligent notification generation
- Human-in-the-loop workflow for approval
- Database persistence with PostgreSQL

## Architecture Note

The application uses a background thread pool for asynchronous task processing. Each worker process maintains its own pool of 5 threads. When running multiple Uvicorn/Gunicorn workers, total concurrency scales accordingly (for example, 2 workers × 5 threads = 10 concurrent background tasks).

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Ollama (for local LLM inference)
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
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=notification_agent

# Security
SECRET_KEY=your-secret-key-here

# Ollama (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b

```

### 4. Initialize the database

Ensure PostgreSQL is running and the database exists, then run migrations:

```bash
# Create database if needed
psql -U postgres -c "CREATE DATABASE notification_agent;"

# Run database migrations
alembic upgrade head
```

### 5. Start the services

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Start the FastAPI application
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Access the interactive API documentation at `http://localhost:8000/docs`.

## API Usage

### Create notification session (async)

Returns immediately with a session ID. The agent processes notifications in the background.

```bash
curl -X POST "http://localhost:8000/api/v1/notification-sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sports",
    "campaign_id": "3be6176f-894a-4c0b-87d1-83b9393fe8cb",
    "company_id": "a639cab1-240b-4d66-b084-751009a88255",
    "admin_id": "22222222-2222-2222-2222-222222222222"
  }'
```

Response:
```json
{
  "session_id": "feb6e46d-3808-4a7d-876b-2a4d4130543f",
  "status": "PROCESSING"
}
```

### Create notification session (sync)

Creates a session and blocks until notifications are generated. Returns the full session with suggestions.

```bash
curl -X POST "http://localhost:8000/api/v1/notification-sessions/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sports",
    "campaign_id": "3be6176f-894a-4c0b-87d1-83b9393fe8cb",
    "company_id": "a639cab1-240b-4d66-b084-751009a88255",
    "admin_id": "22222222-2222-2222-2222-222222222222"
  }'
```

Response includes:
- `all_suggestions`: list of generated notifications, each with `id`, `text`, `news_headline`, and `status`
- `conversation_history`: full conversation with the agent
- `status`: updated to `AWAITING_REVIEW` when complete

### Get notification session

```bash
curl "http://localhost:8000/api/v1/notification-sessions/{session_id}?company_id={company_id}"
```

### Add feedback to a session

```bash
curl -X POST "http://localhost:8000/api/v1/notification-sessions/{session_id}/feedback?company_id={company_id}" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Make the tone more urgent"}'
```

### Publish selected notifications

```bash
curl -X POST "http://localhost:8000/api/v1/notification-sessions/{session_id}/publish?company_id={company_id}" \
  -H "Content-Type: application/json" \
  -d '{"selected_suggestion_ids": ["suggestion-id-1", "suggestion-id-2"]}'
```

## Project Structure

```
.
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   │   └── endpoints/        # Route handlers
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

