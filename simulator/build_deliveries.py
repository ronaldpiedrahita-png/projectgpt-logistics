import random
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Delivery, Order, Truck


def main():
    db: Session = SessionLocal()
    try:
        truck_ids = [row[0] for row in db.execute(select(Truck.id).where(Truck.active.is_(True))).all()]
        if not truck_ids:
            raise ValueError("No hay camiones activos. Ejecuta simulator/generate_gps.py primero.")

        orders = db.execute(
            select(Order).where(Order.status == "pending").order_by(Order.created_at.asc()).limit(30000)
        ).scalars().all()
        if not orders:
            raise ValueError("No hay ordenes pendientes para convertir en entregas.")

        deliveries = []
        for idx, order in enumerate(orders):
            truck_id = random.choice(truck_ids)
            assigned_at = order.created_at + timedelta(minutes=random.randint(5, 45))
            duration = max(20, random.gauss(120, 45))
            delivered_at = assigned_at + timedelta(minutes=duration)

            delivery = Delivery(
                order_id=order.id,
                truck_id=truck_id,
                assigned_at=assigned_at,
                delivered_at=delivered_at,
                delivery_minutes=float(duration),
            )
            deliveries.append(delivery)
            order.status = "delivered"

            if len(deliveries) >= 5000:
                db.bulk_save_objects(deliveries)
                db.commit()
                deliveries = []
                print(f"Procesadas {idx + 1} entregas")

        if deliveries:
            db.bulk_save_objects(deliveries)
            db.commit()

        print(f"Finalizado: {len(orders)} entregas historicas creadas")
    finally:
        db.close()


if __name__ == "__main__":
    main()
