from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.fefo_service import Batch, ProductionDemand, calculate_fefo_plan

app = FastAPI(
    title="FEFO-План API",
    version="0.2.0",
    description="API системы планирования молочного производства по принципу FEFO.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_ORDERS = [
    {"number": "№ 1847", "product": "Творог 5 %", "quantity": "1 200 кг", "delivery_date": "20.09.2026", "status": "Новый", "status_kind": "success"},
    {"number": "№ 1848", "product": "Кефир 2,5 %", "quantity": "900 кг", "delivery_date": "20.09.2026", "status": "В обработке", "status_kind": "warning"},
    {"number": "№ 1849", "product": "Сметана 20 %", "quantity": "650 кг", "delivery_date": "21.09.2026", "status": "В работе", "status_kind": "info"},
]

# В демонстрационной версии эти данные заменят результаты SQL-запроса к PostgreSQL.
INVENTORY_BATCHES = [
    Batch("МЛ-1709", "Молоко нормализованное", 1_200, "A-03-04", date(2026, 9, 21)),
    Batch("МЛ-1809", "Молоко нормализованное", 900, "A-03-05", date(2026, 9, 24)),
    Batch("КФ-1809", "Основа для кефира", 900, "C-02-03", date(2026, 9, 22)),
    Batch("СЛ-1609", "Сливочная основа", 650, "B-01-07", date(2026, 9, 22)),
]

PRODUCTION_DEMANDS = [
    ProductionDemand("Творог 5 %", "Молоко нормализованное", 1_200),
    ProductionDemand("Кефир 2,5 %", "Основа для кефира", 900),
    ProductionDemand("Сметана 20 %", "Сливочная основа", 650),
]

PLAN_REGISTRY: dict[str, dict] = {}


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
    at_risk = [
        {
            "batch": batch.batch_number,
            "product": batch.material,
            "quantity": f"{batch.available_quantity:,} кг".replace(",", " "),
            "location": batch.location,
            "expiry": batch.expiry_date.strftime("%d.%m.%Y"),
            "days_left": (batch.expiry_date - date(2026, 9, 19)).days,
        }
        for batch in sorted(INVENTORY_BATCHES, key=lambda batch: batch.expiry_date)
    ]
    return {
        "date_label": "19 сентября 2026 г.",
        "metrics": [
            {"label": "Заказы на сегодня", "value": "12", "detail": "↑ 3 новых", "kind": "success"},
            {"label": "Рисковые партии", "value": str(len(at_risk)), "detail": "требуют внимания", "kind": "danger"},
            {"label": "Планы на согласовании", "value": "2", "detail": "ожидают решения", "kind": "info"},
            {"label": "Загрузка линии № 2", "value": "78 %", "detail": "в норме", "kind": "success"},
        ],
        "orders": DEMO_ORDERS,
        "at_risk": at_risk,
    }


@app.post("/api/plans/calculate")
def calculate_plan(request: PlanRequest) -> dict:
    """Создаёт проект плана и подбирает партии в порядке FEFO."""
    if request.period_end < request.period_start:
        raise HTTPException(status_code=422, detail="Дата окончания периода не может быть раньше даты начала.")

    line_label = {"all": "Все доступные линии", "line-1": "Линия № 1", "line-2": "Линия № 2"}[request.production_line]
    calculation = calculate_fefo_plan(PRODUCTION_DEMANDS, INVENTORY_BATCHES, request.period_start)
    plan_number = f"PLAN-DEMO-{request.period_start:%Y%m%d}"
    PLAN_REGISTRY[plan_number] = {"status": "draft", "calculation": calculation}

    message = "Проект плана сформирован. Проверьте рекомендации перед утверждением."
    if calculation["shortages"]:
        message = "Проект плана сформирован с предупреждениями о недостатке сырья."

    return {
        "plan_number": plan_number,
        "period": f"{request.period_start:%d.%m.%Y} — {request.period_end:%d.%m.%Y}",
        "production_line": line_label,
        "selected_orders": request.order_count,
        "recommendations": calculation["recommendations"],
        "shortages": calculation["shortages"],
        "summary": {
            "tasks": calculation["tasks"],
            "critical_batches": calculation["critical_batches"],
            "conflicts": calculation["conflicts"],
        },
        "message": message,
    }


@app.post("/api/plans/approve")
def approve_plan(request: ApprovalRequest) -> dict[str, str]:
    """Утверждает предварительно рассчитанный производственный план."""
    plan = PLAN_REGISTRY.get(request.plan_number)
    if plan is None:
        raise HTTPException(status_code=404, detail="План не найден. Сначала выполните расчёт.")
    if plan["calculation"]["conflicts"]:
        raise HTTPException(status_code=409, detail="Нельзя утвердить план с неустранённым дефицитом сырья.")

    plan["status"] = "approved"
    return {"status": "approved", "message": f"План {request.plan_number} утверждён и передан в работу."}


@app.get("/api/batches/at-risk")
def at_risk_batches() -> list[dict]:
    return dashboard()["at_risk"]
