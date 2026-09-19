from datetime import date
import unittest

from app.fefo_service import Batch, ProductionDemand, calculate_fefo_plan


class FefoServiceTests(unittest.TestCase):
    def setUp(self):
        self.reference_date = date(2026, 9, 19)

    def test_uses_batch_with_nearest_expiry_first(self):
        batches = [
            Batch("B-02", "Молоко", 50, "A-02", date(2026, 9, 23)),
            Batch("B-01", "Молоко", 50, "A-01", date(2026, 9, 20)),
        ]
        demands = [ProductionDemand("Творог", "Молоко", 70)]

        result = calculate_fefo_plan(demands, batches, self.reference_date)

        self.assertEqual([item["batch"] for item in result["recommendations"]], ["B-01", "B-02"])
        self.assertEqual([item["volume"] for item in result["recommendations"]], ["50 кг", "20 кг"])
        self.assertEqual(result["conflicts"], 0)

    def test_reports_shortage_when_stock_is_not_enough(self):
        batches = [Batch("B-01", "Закваска", 10, "B-01", date(2026, 9, 22))]
        demands = [ProductionDemand("Кефир", "Закваска", 18)]

        result = calculate_fefo_plan(demands, batches, self.reference_date)

        self.assertEqual(result["shortages"][0]["missing_volume"], "8 кг")
        self.assertEqual(result["conflicts"], 1)


if __name__ == "__main__":
    unittest.main()
