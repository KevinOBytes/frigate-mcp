FROM python:3.12-slim

WORKDIR /app

LABEL io.modelcontextprotocol.server.name="io.github.KevinOBytes/frigate-mcp"

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN pip install --no-cache-dir -e /app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["frigate-mcp", "serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "5000"]