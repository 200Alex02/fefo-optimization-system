import unittest

from fastapi.testclient import TestClient

from app.main import app, repository


class ApiRouteTests(unittest.TestCase):
    def setUp(self):
        repository.clear_plans()
        self.client = TestClient(app)

    def test_health_endpoint_reports_demo_storage(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["storage"], "demo-repository")

    def test_dashboard_and_risk_endpoints_return_consistent_risk_batches(self):
        dashboard_response = self.client.get("/api/dashboard")
        at_risk_response = self.client.get("/api/batches/at-risk")

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(at_risk_response.status_code, 200)
        dashboard = dashboard_response.json()
        self.assertEqual(len(dashboard["at_risk"]), 3)
        self.assertEqual(dashboard["metrics"][1]["value"], "3")
        self.assertEqual(at_risk_response.json(), dashboard["at_risk"])

    def test_calculation_and_approval_complete_through_http_api(self):
        calculation_response = self.client.post(
            "/api/plans/calculate",
            json={
                "period_start": "2026-09-19",
                "period_end": "2026-09-20",
                "production_line": "line-2",
                "order_count": 12,
            },
        )

        self.assertEqual(calculation_response.status_code, 200)
        plan = calculation_response.json()
        self.assertEqual(plan["plan_number"], "PLAN-DEMO-20260919")
        self.assertEqual(plan["recommendations"][0]["batch"], "МЛ-1709")
        self.assertEqual(plan["summary"]["conflicts"], 0)

        approval_response = self.client.post(
            "/api/plans/approve", json={"plan_number": plan["plan_number"]}
        )
        self.assertEqual(approval_response.status_code, 200)
        self.assertEqual(approval_response.json()["status"], "approved")

    def test_calculation_rejects_invalid_planning_period(self):
        response = self.client.post(
            "/api/plans/calculate",
            json={
                "period_start": "2026-09-20",
                "period_end": "2026-09-19",
                "production_line": "all",
                "order_count": 12,
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Дата окончания периода", response.json()["detail"])

    def test_approval_requires_existing_calculation(self):
        response = self.client.post(
            "/api/plans/approve", json={"plan_number": "PLAN-UNKNOWN"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("План не найден", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
