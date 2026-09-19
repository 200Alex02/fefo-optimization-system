from datetime import date
import unittest

from app.main import approve_plan, calculate_plan, repository
from app.schemas import ApprovalRequest, PlanRequest


class ApiLogicTests(unittest.TestCase):
    def setUp(self):
        repository.clear_plans()

    def test_calculate_and_approve_plan(self):
        result = calculate_plan(
            PlanRequest(
                period_start=date(2026, 9, 19),
                period_end=date(2026, 9, 20),
                production_line="line-2",
                order_count=12,
            )
        )

        self.assertEqual(result["plan_number"], "PLAN-DEMO-20260919")
        self.assertEqual(result["production_line"], "Линия № 2")
        self.assertEqual(len(result["recommendations"]), 3)
        self.assertEqual(result["summary"]["conflicts"], 0)
        self.assertEqual(result["recommendations"][0]["batch"], "МЛ-1709")

        approval = approve_plan(ApprovalRequest(plan_number=result["plan_number"]))
        self.assertEqual(approval["status"], "approved")


if __name__ == "__main__":
    unittest.main()
