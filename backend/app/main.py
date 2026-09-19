from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="FEFO-План API",
    version="0.1.0",
    description="Демонстрационный API системы планирования молочного производства по принципу FEFO.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_ORDERS = [
    {
        "number": "№ 1847",
        "product": "Творог 5 %",
        "quantity": "1 200 кг",
        "delivery_date": "20.09.2026",
        "status": "Новый",
        "status_kind": "success",
    },
    {
        "number": "№ 1848",
        "product": "Кефир 2,5 %",
        "quantity": "900 кг",
        "delivery_date": "20.09.2026",
        "status": "В обработке",
        "status_kind": "warning",
    },
    {
        "number": "№ 1849",
        "product": "Сметана 20 %",
        "quantity": "650 кг",
        "delivery_date": "21.09.2026",
        "status": "В работе",
        "status_kind": "info",
    },
]

DEMO_BATCHES = [
    {
        "batch": "МЛ-1709",
        "product": "Молоко нормализованное",
        "quantity": "650 кг",
        "location": "A-03-04",
        "expiry": "21.09.2026",
        "days_left": 1,
    },
    {
        "batch": "СЛ-1609",
        "product": "Сливки 20 %",
        "quantity": "210 кг",
        "location": "B-01-07",
        "expiry": "22.09.2026",
        "days_left": 2,
    },
    {
        "batch": "КФ-1809",
        "product": "Закваска кефирная",
        "quantity": "18 кг",
        "location": "C-02-03",
        "expiry": "22.09.2026",
        "days_left": 2,
    },
]


class PlanRequest(BaseModel):
    period_start: date
    period_end: date
    production_line: Literal["all", "line-1", "line-2"] = "all"
    order_count: int = 12


class ApprovalRequest(BaseModel):
    plan_number: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "FEFO-План API"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    """Возвращает тестовые данные для рабочего стола планировщика."""
    return {
        "date_label": "19 сентября 2026 г.",
        "metrics": [
            {"label": "Заказы на сегодня", "value": "12", "detail": "↑ 3 новых", "kind": "success"},
            {"label": "Рисковые партии", "value": "6", "detail": "требуют внимания", "kind": "danger"},
            {"label": "Планы на согласовании", "value": "2", "detail": "ожидают решения", "kind": "info"},
            {"label": "Загрузка линии № 2", "value": "78 %", "detail": "в норме", "kind": "success"},
        ],
        "orders": DEMO_ORDERS,
        "at_risk": DEMO_BATCHES,
    }


@app.post("/api/plans/calculate")
def calculate_plan(request: PlanRequest) -> dict:
    """Формирует демонстрационный проект плана, выбирая партии в порядке FEFO."""
    line_label = {"all": "Все доступные линии", "line-1": "Линия № 1", "line-2": "Линия № 2"}[request.production_line]
    recommendations = [
        {
            "product": "Творог 5 %",
            "volume": "1 200 кг",
            "batch": "МЛ-1709",
            "location": "A-03-04",
            "expiry": "21.09.2026",
            "priority": "Критичный",
            "priority_kind": "danger",
        },
        {
            "product": "Кефир 2,5 %",
            "volume": "900 кг",
            "batch": "КФ-1809",
            "location": "C-02-03",
            "expiry": "22.09.2026",
            "priority": "Срочный",
            "priority_kind": "warning",
        },
        {
            "product": "Сметана 20 %",
            "volume": "650 кг",
            "batch": "СЛ-1609",
            "location": "B-01-07",
            "expiry": "22.09.2026",
            "priority": "Срочный",
            "priority_kind": "warning",
        },
    ]
    return {
        "plan_number": "PLAN-DEMO-2026-0919",
        "period": f"{request.period_start:%d.%m.%Y} — {request.period_end:%d.%m.%Y}",
        "production_line": line_label,
        "selected_orders": request.order_count,
        "recommendations": recommendations,
        "summary": {"tasks": 3, "critical_batches": 1, "conflicts": 0},
        "message": "Проект плана сформирован. Проверьте рекомендации перед утверждением.",
    }


@app.post("/api/plans/approve")
def approve_plan(request: ApprovalRequest) -> dict[str, str]:
    """Имитирует утверждение сформированного плана."""
    return {
        "status": "approved",
        "message": f"План {request.plan_number} утверждён и передан в работу.",
    }


@app.get("/api/batches/at-risk")
def at_risk_batches() -> list[dict]:
    return DEMO_BATCHES
