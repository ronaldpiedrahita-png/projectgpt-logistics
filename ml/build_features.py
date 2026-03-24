from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

from db.database import engine


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * radius * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def main():
    query = text(
        """
        SELECT
            o.id AS order_id,
            o.created_at,
            o.promised_at,
            o.origin_lat,
            o.origin_lng,
            o.dest_lat,
            o.dest_lng,
            o.weight_kg,
            d.delivery_minutes,
            CASE WHEN d.delivered_at > o.promised_at THEN 1 ELSE 0 END AS late_label
        FROM orders o
        JOIN deliveries d ON d.order_id = o.id
        WHERE d.delivery_minutes IS NOT NULL
        """
    )
    df = pd.read_sql(query, engine)
    if df.empty:
        raise ValueError("No hay datos de entregas para construir features. Ejecuta simulator/build_deliveries.py")

    df["distance_km"] = haversine_km(df["origin_lat"], df["origin_lng"], df["dest_lat"], df["dest_lng"])
    df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
    df["day_of_week"] = pd.to_datetime(df["created_at"]).dt.dayofweek

    features = df[["order_id", "distance_km", "weight_kg", "hour", "day_of_week", "delivery_minutes", "late_label"]]
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    features.to_csv("artifacts/features.csv", index=False)
    print(f"Features generadas: {len(features)} filas en artifacts/features.csv")


if __name__ == "__main__":
    main()
