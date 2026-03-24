# Control Tower Logistica

Proyecto de portafolio de ciencia de datos e ingenieria para operaciones reales de flota y delivery.

## Produccion

- API base: [https://projectgpt-logistics-production.up.railway.app](https://projectgpt-logistics-production.up.railway.app)
- Health: [https://projectgpt-logistics-production.up.railway.app/health](https://projectgpt-logistics-production.up.railway.app/health)
- Swagger UI: [https://projectgpt-logistics-production.up.railway.app/docs](https://projectgpt-logistics-production.up.railway.app/docs)
- ReDoc: [https://projectgpt-logistics-production.up.railway.app/redoc](https://projectgpt-logistics-production.up.railway.app/redoc)

## Que incluye

- API operacional con FastAPI.
- Persistencia en PostgreSQL.
- Simulador de datos historicos (ordenes, GPS, entregas).
- Modelos ML para ETA y riesgo de atraso.
- Optimizacion de asignacion camion-pedido con OR-Tools.
- Docker + CI con GitHub Actions + deploy en Railway.

## Arquitectura

- `api/`: endpoints y contratos de entrada/salida.
- `db/`: conexion SQLAlchemy, esquema y modelos.
- `simulator/`: generacion de datos de negocio.
- `ml/`: features, entrenamiento e inferencia.
- `optimizer/`: optimizacion operacional.
- `scripts/`: ejecucion por etapas (PowerShell).

## Resultados actuales

- Dataset de entrenamiento generado: 30,000 entregas.
- Modelo ETA (RandomForest): MAE = 35.72 min.
- Modelo riesgo atraso (LogisticRegression): AUC = 0.511.
- Validacion en produccion:
  - `POST /orders` OK
  - `GET /orders/{id}/eta` OK
  - Health en Railway: `200 OK`

## Ejecucion local paso a paso

### 1) Bootstrap

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\01_bootstrap.ps1
```

### 2) Variables de entorno

```powershell
Copy-Item .env.example .env -Force
```

`.env.example` usa placeholders seguros. Completa tu password local de PostgreSQL si aplica.

### 3) Infraestructura

```powershell
.\scripts\02_up_infra.ps1
```

Nota: este script levanta Redis en Docker. PostgreSQL se usa desde tu instalacion local.

### 4) Crear base de datos y esquema

```powershell
.\scripts\03_apply_schema.ps1
```

### 5) Simular datos historicos

```powershell
.\scripts\04_seed_data.ps1
```

### 6) Entrenar modelos

```powershell
.\scripts\06_train_ml.ps1
```

### 7) Levantar API

```powershell
.\scripts\05_run_api.ps1
```

## Endpoints principales

- `GET /health`
- `POST /orders`
- `POST /gps-events`
- `POST /optimize-routes`
- `GET /orders/{order_id}/eta`

## Prueba rapida en produccion (PowerShell)

```powershell
$base = "https://projectgpt-logistics-production.up.railway.app"

$now = (Get-Date).ToUniversalTime()
$promised = $now.AddHours(4)

$payload = @{
  created_at = $now.ToString("o")
  promised_at = $promised.ToString("o")
  origin_lat = 4.7110
  origin_lng = -74.0721
  dest_lat = 4.6486
  dest_lng = -74.2479
  weight_kg = 250
  status = "pending"
} | ConvertTo-Json

$order = Invoke-RestMethod -Method POST -Uri "$base/orders" -ContentType "application/json" -Body $payload
$order

Invoke-RestMethod -Method GET -Uri "$base/orders/$($order.id)/eta"
```

## Calidad

```powershell
.\scripts\08_quality.ps1
```

## Docker

```powershell
.\scripts\09_docker_build.ps1
```

## Deploy Railway

```powershell
.\scripts\10_deploy_railway.ps1
```

Si el CLI de Railway no esta disponible globalmente, usa:

```powershell
npx @railway/cli login --browserless
npx @railway/cli init
npx @railway/cli up
```
