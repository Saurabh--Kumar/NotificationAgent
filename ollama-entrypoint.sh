#!/bin/bash
set -e

echo "Waiting for Ollama service to be ready..."
sleep 5

echo "Checking if model '${OLLAMA_MODEL:-gemma4:e2b}' is already pulled..."
if ollama list | grep -q "${OLLAMA_MODEL:-gemma4:e2b}"; then
  echo "Model '${OLLAMA_MODEL:-gemma4:e2b}' already exists. Skipping pull."
else
  echo "Pulling model '${OLLAMA_MODEL:-gemma4:e2b}'..."
  ollama pull "${OLLAMA_MODEL:-gemma4:e2b}"
  echo "Model pulled successfully!"
fi

echo "Ollama is ready with model '${OLLAMA_MODEL:-gemma4:e2b}'"
exec ollama serve
