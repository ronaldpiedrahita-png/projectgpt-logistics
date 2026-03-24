$ErrorActionPreference = "Stop"
# Solo Redis en Docker. PostgreSQL se usa desde tu instalacion local.
docker compose up -d redis
docker compose ps
