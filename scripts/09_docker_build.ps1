$ErrorActionPreference = "Stop"
docker build -t logistics-api:latest .
docker compose up -d
docker compose ps
