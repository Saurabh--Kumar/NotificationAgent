# AI Notification Generation Agent

A scalable, multi-tenant service for generating context-aware notifications using AI.

## Video Demo

**Watch the demo:** [https://youtu.be/PVdfmS1AIRw](https://youtu.be/PVdfmS1AIRw)

## Project Overview

This project implements a full-stack application that allows B2C enterprise customers to generate timely, context-aware notifications for their end-users. The backend exposes a RESTful API and background agent, while the admin UI provides a human-in-the-loop workflow for reviewing and publishing AI-generated notification suggestions based on real-time news, company campaigns, and brand identity.

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

- Python 3.12+
- PostgreSQL 16+
- Ollama (for local LLM inference)
- (Optional) Docker and Docker Compose

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd NotificationAgent
```

### 2. Docker Setup (Recommended)

The easiest way to run the full stack is with Docker Compose. This will automatically start PostgreSQL, Ollama, and the web application with all dependencies.

**Important:** Run these commands from the project root directory (where `docker-compose.yml` is located).

#### First Run (Model Download Required)

On the first run, the `gemma4:e2b` model (~7.1 GB) will be downloaded automatically. This can take several minutes depending on your internet speed.

```bash
# Build and start all services (foreground mode to see progress)
docker compose build --no-cache
docker compose up
```

**Why `docker compose up` without `-d`?** The web container must download the Ollama model on first run. Running in foreground mode shows real-time download progress and blocks until the app is fully ready. You'll see logs like:
```
web-1  | {"status":"pulling 4e30e2665218","total":7162394016,"completed":...}
web-1  | {"status":"success"}
web-1  | Running database setup...
web-1  | Starting application...
web-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

Once you see `Uvicorn running`, the app is ready. Press `Ctrl+C` to stop the containers.

#### Subsequent Runs

After the model is downloaded, you can use detached mode:

```bash
docker compose up -d
```

#### View Logs

```bash
# Follow web container logs
docker compose logs -f web

# Check Ollama container logs
docker compose logs ollama

# Check database container logs
docker compose logs db
```

#### Stop Services

```bash
docker compose down
```

#### What Docker Compose Sets Up

- **PostgreSQL 16** database with persistent storage
- **Ollama** with the `gemma4:e2b` model auto-pulled on first run
- **Web application** with automatic database initialization and seed data
- All services are orchestrated with healthchecks and restart policies

#### Container Status vs App Readiness

- `docker compose ps` showing `State: Up` means the container process is running
- The app may still be initializing (downloading model, running DB setup)
- Use `docker compose logs web` to see actual app status
- The health endpoint at `http://localhost:8000/health` returns 200 only when the app is fully ready

#### Access the Application

- Admin UI: `http://localhost:8000/static/admin.html`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Manual Setup (Alternative)

If you prefer to run without Docker, follow these steps:

#### Set up the environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure environment variables

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

#### Initialize the database

Ensure PostgreSQL is running, then run the database setup script:

```bash
# Create database, tables, and seed dummy campaigns
python scripts/setup_db.py
```

The database schema is defined in [`schema/db_schema.sql`](schema/db_schema.sql) and managed through the setup script.

#### Start the services

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Start the FastAPI application
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Access the interactive API documentation at `http://localhost:8000/docs`.

## Admin UI

The admin UI is available at `http://localhost:8000/static/admin.html`.

### Features
- **Company dropdown**: Shows distinct company names derived from the campaigns table
- **Campaign dropdown**: Shows only active campaigns for the selected company
- **Topic selector**: Choose from agriculture, sports, business, technologies, or latest
- **Campaign details panel**: Displays full campaign information when a campaign is selected
- **Generate button**: Creates a notification generation session
- **Loading state + polling**: Polls every 20 seconds to accommodate local LLM generation (6-8 minutes)
- **Suggestion list**: Shows generated notifications with checkboxes and the news headline used for generation
- **Selected area**: Accumulates selected notifications across generations
- **Publish button**: Publishes selected notifications

### UI Flow
1. Select a company from the dropdown
2. Select an active campaign from the dropdown
3. Review the campaign details panel
4. Select a topic
5. Click "Generate Notifications"
6. Wait for generation to complete (polling every 20 seconds)
7. Check the suggestions you want to publish
8. Click "Publish Selected"

## API Usage

### Get Companies

Fetch distinct companies derived from the campaigns table.

```bash
curl -X GET "http://localhost:8000/api/v1/companies"
```

### Get Active Campaigns

Fetch active campaigns for a specific company.

```bash
curl -X GET "http://localhost:8000/api/v1/companies/{company_id}/campaigns"
```

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

Creates a session and blocks until notifications are generated. Returns the session ID, status, and generated suggestions.

```bash
curl -X POST "http://localhost:8000/api/v1/company/a639cab1-240b-4d66-b084-751009a88255/notification/sync" \
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
curl "http://localhost:8000/api/v1/company/{company_id}/notification-sessions/{session_id}"
```

### Add feedback to a session

```bash
curl -X POST "http://localhost:8000/api/v1/company/{company_id}/notification-sessions/{session_id}/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Make the tone more urgent"}'
```

### Publish selected notifications

```bash
curl -X POST "http://localhost:8000/api/v1/company/{company_id}/notification-sessions/{session_id}/publish" \
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
├── schema/                   # Database schema SQL
├── scripts/                  # Database setup scripts
├── static/                   # Static files (admin UI)
├── tests/                    # Test files
├── .env.example              # Environment variable template
├── .gitignore
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

### Database Setup

```bash
# Create database, tables, and seed dummy campaigns
python scripts/setup_db.py
```

The database schema is defined in [`schema/db_schema.sql`](schema/db_schema.sql).

## API Documentation

API documentation is available at:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

