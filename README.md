# Control Tower Logistica (Scaffold Completo)

Proyecto de portafolio de nivel profesional para una operacion de flota/delivery:

- API operacional en FastAPI.
- Persistencia en PostgreSQL (compatible con PostGIS).
- Simulacion de datos historicos.
- Entrenamiento de modelos ML (ETA y riesgo de atraso).
- Optimizacion de asignacion camion-pedido con OR-Tools.
- Docker, CI/CD con GitHub Actions y deploy en Railway.

## 1. Levantar infraestructura local

```powershell
copy .env.example .env
./scripts/02_up_infra.ps1
./scripts/03_apply_schema.ps1
```

## 2. Instalar dependencias

```powershell
./scripts/01_bootstrap.ps1
```

## 3. Generar datos de entrenamiento

```powershell
./scripts/04_seed_data.ps1
```

## 4. Entrenar modelos

```powershell
./scripts/06_train_ml.ps1
```

## 5. Ejecutar API

```powershell
./scripts/05_run_api.ps1
```

### Endpoints principales

- `GET /health`
- `POST /orders`
- `POST /gps-events`
- `POST /optimize-routes`
- `GET /orders/{order_id}/eta`

## 6. Calidad y tests

```powershell
./scripts/08_quality.ps1
```

## 7. Docker y deploy

```powershell
./scripts/09_docker_build.ps1
./scripts/10_deploy_railway.ps1
```

## Arquitectura (resumen)

- `api/`: endpoints y validacion de entrada/salida.
- `db/`: conexion SQLAlchemy, modelos y script SQL.
- `simulator/`: generacion de ordenes, GPS y entregas historicas.
- `ml/`: pipeline de features, entrenamiento e inferencia.
- `optimizer/`: motor de optimizacion para asignar pedidos a camiones.
- `scripts/`: etapas automatizadas para presentar el proyecto de forma profesional.
