#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U postgres; do
  echo "Database is not ready yet. Waiting..."
  sleep 2
done
echo "Database is ready!"

echo "Waiting for Ollama to be ready..."
until curl -s http://ollama:11434/api/tags > /dev/null; do
  echo "Ollama is not ready yet. Waiting..."
  sleep 2
done
echo "Ollama is ready!"

echo "Pulling Ollama model..."
curl -X POST http://ollama:11434/api/pull -d '{"name": "gemma4:e2b"}'

echo "Running database setup..."
python scripts/setup_db.py

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
