"""Pydantic-модели HTTP-запросов backend-части."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class PlanRequest(BaseModel):
    period_start: date
    period_end: date
    production_line: Literal["all", "line-1", "line-2"] = "all"
    order_count: int = 12


class ApprovalRequest(BaseModel):
    plan_number: str
