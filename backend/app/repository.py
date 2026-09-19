"""Репозиторий демонстрационных данных и проектов производственных планов."""

from __future__ import annotations

from copy import deepcopy
from datetime import date

from app.fefo_service import Batch, ProductionDemand


class DemoPlanningRepository:
    """Изолирует API от способа хранения данных.

    В демонстрационной версии используется оперативная память. При подключении
    PostgreSQL методы этого класса заменяются запросами к таблицам базы данных
    без изменения HTTP-маршрутов и FEFO-алгоритма.
    """

    def __init__(self) -> None:
        self._plans: dict[str, dict] = {}
        self._orders = [
            {"number": "№ 1847", "product": "Творог 5 %", "quantity": "1 200 кг", "delivery_date": "20.09.2026", "status": "Новый", "status_kind": "success"},
            {"number": "№ 1848", "product": "Кефир 2,5 %", "quantity": "900 кг", "delivery_date": "20.09.2026", "status": "В обработке", "status_kind": "warning"},
            {"number": "№ 1849", "product": "Сметана 20 %", "quantity": "650 кг", "delivery_date": "21.09.2026", "status": "В работе", "status_kind": "info"},
        ]
        self._batches = [
            Batch("МЛ-1709", "Молоко нормализованное", 1_200, "A-03-04", date(2026, 9, 21)),
            Batch("МЛ-1809", "Молоко нормализованное", 900, "A-03-05", date(2026, 9, 24)),
            Batch("КФ-1809", "Основа для кефира", 900, "C-02-03", date(2026, 9, 22)),
            Batch("СЛ-1609", "Сливочная основа", 650, "B-01-07", date(2026, 9, 22)),
        ]
        self._demands = [
            ProductionDemand("Творог 5 %", "Молоко нормализованное", 1_200),
            ProductionDemand("Кефир 2,5 %", "Основа для кефира", 900),
            ProductionDemand("Сметана 20 %", "Сливочная основа", 650),
        ]

    def get_calculation_inputs(self) -> tuple[list[ProductionDemand], list[Batch]]:
        return list(self._demands), list(self._batches)

    def get_dashboard(self, reference_date: date) -> dict:
        at_risk = [
            {
                "batch": batch.batch_number,
                "product": batch.material,
                "quantity": f"{batch.available_quantity:,} кг".replace(",", " "),
                "location": batch.location,
                "expiry": batch.expiry_date.strftime("%d.%m.%Y"),
                "days_left": (batch.expiry_date - reference_date).days,
            }
            for batch in sorted(self._batches, key=lambda item: item.expiry_date)
        ]
        return {
            "date_label": reference_date.strftime("%d сентября %Y г."),
            "metrics": [
                {"label": "Заказы на сегодня", "value": "12", "detail": "↑ 3 новых", "kind": "success"},
                {"label": "Рисковые партии", "value": str(len(at_risk)), "detail": "требуют внимания", "kind": "danger"},
                {"label": "Планы на согласовании", "value": "2", "detail": "ожидают решения", "kind": "info"},
                {"label": "Загрузка линии № 2", "value": "78 %", "detail": "в норме", "kind": "success"},
            ],
            "orders": deepcopy(self._orders),
            "at_risk": at_risk,
        }

    def save_draft(self, plan_number: str, calculation: dict) -> None:
        self._plans[plan_number] = {"status": "draft", "calculation": deepcopy(calculation)}

    def get_plan(self, plan_number: str) -> dict | None:
        plan = self._plans.get(plan_number)
        return deepcopy(plan) if plan else None

    def approve_plan(self, plan_number: str) -> bool:
        plan = self._plans.get(plan_number)
        if plan is None:
            return False
        plan["status"] = "approved"
        return True

    def clear_plans(self) -> None:
        self._plans.clear()
