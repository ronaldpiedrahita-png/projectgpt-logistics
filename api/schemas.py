from datetime import datetime

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    created_at: datetime
    promised_at: datetime
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    weight_kg: float = Field(gt=0)
    status: str = "pending"


class OrderOut(BaseModel):
    id: int
    created_at: datetime
    promised_at: datetime
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    weight_kg: float
    status: str

    model_config = {"from_attributes": True}


class GPSEventCreate(BaseModel):
    truck_id: int
    event_time: datetime
    lat: float
    lng: float
    speed_kmh: float | None = None
    fuel_level: float | None = None


class OptimizeRequest(BaseModel):
    date: datetime | None = None
    persist_assignments: bool = True


class OptimizeResponse(BaseModel):
    total_assigned: int
    assignments: list[dict]


class ETAResponse(BaseModel):
    order_id: int
    predicted_eta_minutes: float
    late_risk: float
    model_version: str
