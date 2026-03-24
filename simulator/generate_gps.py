import argparse
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import GPSEvent, Truck


def ensure_trucks(db: Session, total: int = 80):
    existing = db.execute(select(Truck.id)).all()
    if existing:
        return
    for i in range(total):
        truck = Truck(
            plate=f"TRK-{i:04d}",
            capacity_kg=random.choice([1500, 2000, 3000, 5000, 7000]),
            active=True,
        )
        db.add(truck)
    db.commit()
    print(f"Camiones creados: {total}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--rows", type=int, default=200000)
    args = parser.parse_args()

    now = datetime.utcnow()
    base_lat, base_lng = 4.7110, -74.0721

    db: Session = SessionLocal()
    try:
        ensure_trucks(db)
        truck_ids = [row[0] for row in db.execute(select(Truck.id).where(Truck.active.is_(True))).all()]

        batch = []
        for i in range(args.rows):
            event_time = now - timedelta(
                days=random.randint(0, args.days),
                minutes=random.randint(0, 1440),
            )
            event = GPSEvent(
                truck_id=random.choice(truck_ids),
                event_time=event_time,
                lat=base_lat + random.uniform(-0.3, 0.3),
                lng=base_lng + random.uniform(-0.4, 0.4),
                speed_kmh=round(max(0.0, random.gauss(42, 12)), 2),
                fuel_level=round(random.uniform(10, 100), 2),
            )
            batch.append(event)
            if len(batch) >= 10000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"Insertados {i + 1} eventos GPS")

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
        print(f"Finalizado: {args.rows} eventos GPS generados")
    finally:
        db.close()


if __name__ == "__main__":
    main()
