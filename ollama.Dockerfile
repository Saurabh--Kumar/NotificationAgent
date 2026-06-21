FROM ollama/ollama:latest

# Copy custom entrypoint
COPY ollama-entrypoint.sh /ollama-entrypoint.sh
RUN chmod +x /ollama-entrypoint.sh

# Use custom entrypoint that pulls the model on first run
ENTRYPOINT ["/ollama-entrypoint.sh"]
