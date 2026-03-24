import argparse
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Order


def random_coord(center: float, spread: float) -> float:
    return center + random.uniform(-spread, spread)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--rows", type=int, default=50000)
    args = parser.parse_args()

    now = datetime.utcnow()
    base_lat, base_lng = 4.7110, -74.0721

    db: Session = SessionLocal()
    try:
        batch = []
        for i in range(args.rows):
            created_at = now - timedelta(
                days=random.randint(0, args.days),
                minutes=random.randint(0, 1440),
            )
            promised_at = created_at + timedelta(minutes=random.randint(45, 900))
            order = Order(
                created_at=created_at,
                promised_at=promised_at,
                origin_lat=random_coord(base_lat, 0.15),
                origin_lng=random_coord(base_lng, 0.2),
                dest_lat=random_coord(base_lat, 0.25),
                dest_lng=random_coord(base_lng, 0.3),
                weight_kg=round(random.uniform(5, 2500), 2),
                status="pending",
            )
            batch.append(order)
            if len(batch) >= 5000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"Insertadas {i + 1} ordenes")

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
        print(f"Finalizado: {args.rows} ordenes generadas")
    finally:
        db.close()


if __name__ == "__main__":
    main()
