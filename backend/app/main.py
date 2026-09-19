from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.fefo_service import calculate_fefo_plan
from app.repository import DemoPlanningRepository
from app.schemas import ApprovalRequest, PlanRequest

app = FastAPI(
    title="FEFO-План API",
    version="0.3.0",
    description="API системы планирования молочного производства по принципу FEFO.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = DemoPlanningRepository()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "FEFO-План API", "storage": "demo-repository"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    """Возвращает показатели, заказы и рисковые партии для рабочего стола."""
    return repository.get_dashboard(reference_date=date(2026, 9, 19))


@app.post("/api/plans/calculate")
def calculate_plan(request: PlanRequest) -> dict:
    """Создаёт проект плана и подбирает партии в порядке FEFO."""
    if request.period_end < request.period_start:
        raise HTTPException(status_code=422, detail="Дата окончания периода не может быть раньше даты начала.")

    line_label = {"all": "Все доступные линии", "line-1": "Линия № 1", "line-2": "Линия № 2"}[request.production_line]
    demands, batches = repository.get_calculation_inputs()
    calculation = calculate_fefo_plan(demands, batches, request.period_start)
    plan_number = f"PLAN-DEMO-{request.period_start:%Y%m%d}"
    repository.save_draft(plan_number, calculation)

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
    plan = repository.get_plan(request.plan_number)
    if plan is None:
        raise HTTPException(status_code=404, detail="План не найден. Сначала выполните расчёт.")
    if plan["calculation"]["conflicts"]:
        raise HTTPException(status_code=409, detail="Нельзя утвердить план с неустранённым дефицитом сырья.")

    repository.approve_plan(request.plan_number)
    return {"status": "approved", "message": f"План {request.plan_number} утверждён и передан в работу."}


@app.get("/api/batches/at-risk")
def at_risk_batches() -> list[dict]:
    return dashboard()["at_risk"]
