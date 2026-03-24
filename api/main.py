import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
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
from db.models import Base, EtaPrediction, GPSEvent, Order
from ml.inference import predict_for_order
from optimizer.run_optimizer import optimize_assignments

app = FastAPI(title="Logistics Control Tower API", version="0.1.0")


@app.on_event("startup")
def startup_init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "env": os.getenv("ENV", "development")}


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
    run_date = payload.date or datetime.utcnow()
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
