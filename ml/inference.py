import json
from pathlib import Path

import joblib
import numpy as np


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    return float(2 * radius * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))


def _feature_row(order) -> np.ndarray:
    distance_km = haversine_km(order.origin_lat, order.origin_lng, order.dest_lat, order.dest_lng)
    hour = order.created_at.hour
    day_of_week = order.created_at.weekday()
    return np.array([[distance_km, order.weight_kg, hour, day_of_week]])


def predict_for_order(order):
    model_dir = Path("artifacts")
    eta_model_path = model_dir / "eta_model.joblib"
    late_model_path = model_dir / "late_risk_model.joblib"
    metadata_path = model_dir / "model_metadata.json"

    if eta_model_path.exists() and late_model_path.exists():
        eta_model = joblib.load(eta_model_path)
        late_model = joblib.load(late_model_path)
        row = _feature_row(order)

        predicted_eta = float(eta_model.predict(row)[0])
        if hasattr(late_model, "predict_proba"):
            late_risk = float(late_model.predict_proba(row)[0][1])
        else:
            late_risk = float(np.clip(late_model.predict(row)[0], 0.0, 1.0))
    else:
        distance_km = haversine_km(order.origin_lat, order.origin_lng, order.dest_lat, order.dest_lng)
        predicted_eta = max(20.0, distance_km * 3.0 + order.weight_kg * 0.02)
        late_risk = float(np.clip((predicted_eta - 90.0) / 120.0, 0.05, 0.95))

    model_version = "baseline-fallback"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_version = metadata.get("model_version", model_version)
    return predicted_eta, late_risk, model_version
