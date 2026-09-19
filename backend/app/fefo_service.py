"""Прикладная логика формирования производственного плана по правилу FEFO."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class Batch:
    """Доступная партия материала на складе."""

    batch_number: str
    material: str
    available_quantity: int
    location: str
    expiry_date: date


@dataclass(frozen=True)
class ProductionDemand:
    """Потребность производства в конкретном материале для выпуска продукции."""

    product: str
    material: str
    required_quantity: int


def urgency_for(expiry_date: date, reference_date: date) -> tuple[str, str]:
    """Возвращает пользовательский приоритет по числу дней до окончания срока годности."""
    days_left = (expiry_date - reference_date).days
    if days_left <= 2:
        return "Критичный", "danger"
    if days_left <= 4:
        return "Срочный", "warning"
    return "Плановый", "info"


def calculate_fefo_plan(
    demands: Iterable[ProductionDemand],
    batches: Iterable[Batch],
    reference_date: date,
) -> dict:
    """Распределяет доступные партии между производственными потребностями.

    Для каждой потребности выбираются активные партии требуемого материала,
    отсортированные по возрастанию срока годности. Из партии резервируется
    минимальное из двух значений: требуемый остаток или доступный объём.
    Алгоритм поддерживает частичный отбор партии и формирует предупреждение,
    если требуемого объёма недостаточно.
    """
    demands = list(demands)
    batches = list(batches)
    remaining_by_batch = {batch.batch_number: batch.available_quantity for batch in batches}
    batches_by_material: dict[str, list[Batch]] = {}
    for batch in batches:
        if batch.available_quantity <= 0:
            continue
        batches_by_material.setdefault(batch.material, []).append(batch)

    for material_batches in batches_by_material.values():
        material_batches.sort(key=lambda batch: (batch.expiry_date, batch.batch_number))

    recommendations: list[dict] = []
    shortages: list[dict] = []
    critical_batches: set[str] = set()

    for demand in demands:
        required_left = demand.required_quantity
        candidates = batches_by_material.get(demand.material, [])
        for batch in candidates:
            if required_left == 0:
                break

            quantity_available = remaining_by_batch[batch.batch_number]
            if quantity_available == 0:
                continue

            quantity_to_reserve = min(required_left, quantity_available)
            priority, priority_kind = urgency_for(batch.expiry_date, reference_date)
            recommendations.append(
                {
                    "product": demand.product,
                    "material": demand.material,
                    "volume": f"{quantity_to_reserve:,} кг".replace(",", " "),
                    "batch": batch.batch_number,
                    "location": batch.location,
                    "expiry": batch.expiry_date.strftime("%d.%m.%Y"),
                    "priority": priority,
                    "priority_kind": priority_kind,
                }
            )
            if priority_kind == "danger":
                critical_batches.add(batch.batch_number)

            remaining_by_batch[batch.batch_number] -= quantity_to_reserve
            required_left -= quantity_to_reserve

        if required_left > 0:
            shortages.append(
                {
                    "product": demand.product,
                    "material": demand.material,
                    "missing_volume": f"{required_left:,} кг".replace(",", " "),
                }
            )

    return {
        "recommendations": recommendations,
        "shortages": shortages,
        "critical_batches": len(critical_batches),
        "conflicts": len(shortages),
        "tasks": len(demands),
    }
