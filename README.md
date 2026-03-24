# Control Tower Logistica

Proyecto de portfolio de ciencia de datos e ingenieria para operaciones reales de flota y delivery.

## Produccion

- Web V2: [https://projectgpt-logistics-production.up.railway.app](https://projectgpt-logistics-production.up.railway.app)
- API Docs: [https://projectgpt-logistics-production.up.railway.app/docs](https://projectgpt-logistics-production.up.railway.app/docs)
- Health: [https://projectgpt-logistics-production.up.railway.app/health](https://projectgpt-logistics-production.up.railway.app/health)

## Novedades V2 Full

- Dashboard visual premium en `/`.
- KPIs en vivo (ordenes, camiones activos, ETA promedio, on-time rate).
- Mapa de ordenes recientes (Leaflet).
- Grafica de actividad de 7 dias (Chart.js).
- Tabla operativa de ultimas ordenes.
- Panel para crear ordenes y consultar ETA desde la web.

## Endpoints principales

- `GET /health`
- `POST /orders`
- `GET /orders/{order_id}/eta`
- `POST /gps-events`
- `POST /optimize-routes`

## Endpoints dashboard V2

- `GET /dashboard/summary`
- `GET /dashboard/activity?days=7`
- `GET /dashboard/recent-orders?limit=40`

## Arquitectura

- `api/`: FastAPI + endpoints operativos y de dashboard.
- `db/`: SQLAlchemy, modelos y scripts de setup.
- `ml/`: features, entrenamiento e inferencia ETA/riesgo.
- `optimizer/`: asignacion camion-pedido con OR-Tools.
- `simulator/`: generador de datos historicos.
- `web/`: frontend V2 (HTML/CSS/JS).
- `scripts/`: ejecucion paso a paso (PowerShell).

## Resultados actuales

- Dataset de entrenamiento: 30,000 entregas.
- Modelo ETA (RandomForest): MAE = 35.72 min.
- Riesgo de atraso (LogisticRegression): AUC = 0.511.

## Ejecucion local

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\01_bootstrap.ps1
Copy-Item .env.example .env -Force
.\scripts\02_up_infra.ps1
.\scripts\03_apply_schema.ps1
.\scripts\04_seed_data.ps1
.\scripts\06_train_ml.ps1
.\scripts\05_run_api.ps1
```

## Calidad

```powershell
.\scripts\08_quality.ps1
```

## Deploy Railway

```powershell
.\scripts\10_deploy_railway.ps1
```

Si no tienes CLI global:

```powershell
npx @railway/cli login --browserless
npx @railway/cli init
npx @railway/cli up
```
