from __future__ import annotations

from datetime import datetime

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.models import Delivery

try:
    from ortools.linear_solver import pywraplp
except Exception:
    pywraplp = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    return float(2 * radius * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))


def _load_data(db: Session):
    orders = db.execute(
        text(
            """
            SELECT id, weight_kg, dest_lat, dest_lng
            FROM orders
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 200
            """
        )
    ).mappings().all()

    trucks = db.execute(
        text(
            """
            SELECT t.id, t.capacity_kg,
                   COALESCE(g.lat, 4.7110) AS lat,
                   COALESCE(g.lng, -74.0721) AS lng
            FROM trucks t
            LEFT JOIN LATERAL (
              SELECT ge.lat, ge.lng
              FROM gps_events ge
              WHERE ge.truck_id = t.id
              ORDER BY ge.event_time DESC
              LIMIT 1
            ) g ON true
            WHERE t.active = true
            ORDER BY t.id ASC
            """
        )
    ).mappings().all()
    return orders, trucks


def _greedy_assign(orders, trucks):
    assignments = []
    remaining = {t["id"]: float(t["capacity_kg"]) for t in trucks}
    for order in orders:
        candidates = [t for t in trucks if remaining[t["id"]] >= float(order["weight_kg"])]
        if not candidates:
            continue
        best_truck = min(
            candidates,
            key=lambda t: haversine_km(t["lat"], t["lng"], order["dest_lat"], order["dest_lng"]),
        )
        remaining[best_truck["id"]] -= float(order["weight_kg"])
        assignments.append({"order_id": int(order["id"]), "truck_id": int(best_truck["id"])})
    return assignments


def _ortools_assign(orders, trucks):
    if not pywraplp:
        return _greedy_assign(orders, trucks)

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        return _greedy_assign(orders, trucks)

    x = {}
    for o_idx, _order in enumerate(orders):
        for t_idx, _truck in enumerate(trucks):
            x[(o_idx, t_idx)] = solver.BoolVar(f"x_{o_idx}_{t_idx}")

    for o_idx, _order in enumerate(orders):
        solver.Add(sum(x[(o_idx, t_idx)] for t_idx in range(len(trucks))) <= 1)

    for t_idx, truck in enumerate(trucks):
        solver.Add(
            sum(x[(o_idx, t_idx)] * float(orders[o_idx]["weight_kg"]) for o_idx in range(len(orders)))
            <= float(truck["capacity_kg"])
        )

    objective = solver.Objective()
    for o_idx, order in enumerate(orders):
        for t_idx, truck in enumerate(trucks):
            cost = haversine_km(truck["lat"], truck["lng"], order["dest_lat"], order["dest_lng"])
            objective.SetCoefficient(x[(o_idx, t_idx)], -cost)
    objective.SetMaximization()

    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return _greedy_assign(orders, trucks)

    assignments = []
    for o_idx, order in enumerate(orders):
        for t_idx, truck in enumerate(trucks):
            if x[(o_idx, t_idx)].solution_value() > 0.5:
                assignments.append({"order_id": int(order["id"]), "truck_id": int(truck["id"])})
                break
    return assignments


def optimize_assignments(db: Session, run_date: datetime, persist: bool = True):
    _ = run_date
    orders, trucks = _load_data(db)
    if not orders or not trucks:
        return []

    assignments = _ortools_assign(orders, trucks)

    if persist:
        for item in assignments:
            delivery = Delivery(
                order_id=item["order_id"],
                truck_id=item["truck_id"],
                assigned_at=datetime.utcnow(),
                delivered_at=None,
                delivery_minutes=None,
            )
            db.add(delivery)
            db.execute(
                text("UPDATE orders SET status='assigned' WHERE id = :order_id"),
                {"order_id": item["order_id"]},
            )
        db.commit()

    return assignments
