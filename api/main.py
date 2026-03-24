import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.schemas import (
    ETAResponse,
    GPSEventCreate,
    OptimizeRequest,
    OptimizeResponse,
    OrderCreate,
    OrderOut,
)
from db.database import SessionLocal, engine
from db.models import Base, Delivery, EtaPrediction, GPSEvent, Order, Truck
from ml.inference import predict_for_order
from optimizer.run_optimizer import optimize_assignments

app = FastAPI(title="Logistics Control Tower API", version="0.2.0")

BASE_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = BASE_DIR / "web"

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@app.on_event("startup")
def startup_init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def web_home():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_file)


@app.get("/health")
def health():
    return {"status": "ok", "env": os.getenv("ENV", "development")}


@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    now = _utcnow_naive()
    last_24h = now - timedelta(hours=24)

    total_orders = int(db.query(func.count(Order.id)).scalar() or 0)
    active_trucks = int(db.query(func.count(Truck.id)).filter(Truck.active.is_(True)).scalar() or 0)

    status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    by_status = {status: int(count) for status, count in status_rows}

    avg_eta, avg_late_risk, prediction_count = db.query(
        func.avg(EtaPrediction.predicted_eta_minutes),
        func.avg(EtaPrediction.late_risk),
        func.count(EtaPrediction.id),
    ).one()

    deliveries_24h = int(
        db.query(func.count(Delivery.id))
        .filter(Delivery.delivered_at.is_not(None), Delivery.delivered_at >= last_24h)
        .scalar()
        or 0
    )

    completed_total = int(
        db.query(func.count(Delivery.id))
        .join(Order, Delivery.order_id == Order.id)
        .filter(Delivery.delivered_at.is_not(None))
        .scalar()
        or 0
    )

    completed_on_time = int(
        db.query(func.count(Delivery.id))
        .join(Order, Delivery.order_id == Order.id)
        .filter(Delivery.delivered_at.is_not(None), Delivery.delivered_at <= Order.promised_at)
        .scalar()
        or 0
    )

    on_time_rate = 0.0
    if completed_total > 0:
        on_time_rate = round((completed_on_time / completed_total) * 100.0, 2)

    return {
        "total_orders": total_orders,
        "active_trucks": active_trucks,
        "by_status": by_status,
        "avg_eta_minutes": round(float(avg_eta), 2) if avg_eta is not None else None,
        "avg_late_risk": round(float(avg_late_risk), 3) if avg_late_risk is not None else None,
        "prediction_count": int(prediction_count or 0),
        "deliveries_24h": deliveries_24h,
        "on_time_rate": on_time_rate,
    }


@app.get("/dashboard/activity")
def dashboard_activity(days: int = Query(default=7, ge=3, le=30), db: Session = Depends(get_db)):
    now = _utcnow_naive().date()
    start = now - timedelta(days=days - 1)

    timeline = {}
    for i in range(days):
        day = start + timedelta(days=i)
        key = day.isoformat()
        timeline[key] = {"date": key, "total": 0, "pending": 0, "assigned": 0, "delivered": 0}

    rows = db.query(Order.created_at, Order.status).filter(Order.created_at >= datetime.combine(start, datetime.min.time())).all()
    for created_at, status in rows:
        if created_at is None:
            continue
        key = created_at.date().isoformat()
        if key not in timeline:
            continue
        timeline[key]["total"] += 1
        if status in ("pending", "assigned", "delivered"):
            timeline[key][status] += 1

    return {"days": days, "series": list(timeline.values())}


@app.get("/dashboard/recent-orders")
def dashboard_recent_orders(limit: int = Query(default=30, ge=5, le=120), db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
    order_ids = [order.id for order in orders]

    prediction_map = {}
    if order_ids:
        prediction_rows = (
            db.query(EtaPrediction)
            .filter(EtaPrediction.order_id.in_(order_ids))
            .order_by(EtaPrediction.order_id.asc(), EtaPrediction.predicted_at.desc())
            .all()
        )
        for row in prediction_rows:
            if row.order_id not in prediction_map:
                prediction_map[row.order_id] = row

    payload = []
    for order in orders:
        prediction = prediction_map.get(order.id)
        payload.append(
            {
                "id": int(order.id),
                "created_at": order.created_at.isoformat(),
                "status": order.status,
                "weight_kg": float(order.weight_kg),
                "origin": {"lat": float(order.origin_lat), "lng": float(order.origin_lng)},
                "destination": {"lat": float(order.dest_lat), "lng": float(order.dest_lng)},
                "eta_minutes": float(prediction.predicted_eta_minutes) if prediction else None,
                "late_risk": float(prediction.late_risk) if prediction else None,
            }
        )

    return {"count": len(payload), "orders": payload}


@app.post("/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.post("/gps-events")
def create_gps_event(payload: GPSEventCreate, db: Session = Depends(get_db)):
    event = GPSEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "truck_id": event.truck_id}


@app.post("/optimize-routes", response_model=OptimizeResponse)
def optimize_routes(payload: OptimizeRequest, db: Session = Depends(get_db)):
    run_date = payload.date or _utcnow_naive()
    assignments = optimize_assignments(db=db, run_date=run_date, persist=payload.persist_assignments)
    return OptimizeResponse(total_assigned=len(assignments), assignments=assignments)


@app.get("/orders/{order_id}/eta", response_model=ETAResponse)
def get_order_eta(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    latest_prediction = db.execute(
        select(EtaPrediction).where(EtaPrediction.order_id == order_id).order_by(EtaPrediction.predicted_at.desc())
    ).scalar_one_or_none()

    if latest_prediction:
        return ETAResponse(
            order_id=order_id,
            predicted_eta_minutes=float(latest_prediction.predicted_eta_minutes),
            late_risk=float(latest_prediction.late_risk),
            model_version=latest_prediction.model_version or "unknown",
        )

    predicted_eta, late_risk, model_version = predict_for_order(order)
    record = EtaPrediction(
        order_id=order.id,
        predicted_eta_minutes=predicted_eta,
        late_risk=late_risk,
        model_version=model_version,
    )
    db.add(record)
    db.commit()

    return ETAResponse(
        order_id=order.id,
        predicted_eta_minutes=predicted_eta,
        late_risk=late_risk,
        model_version=model_version,
    )
