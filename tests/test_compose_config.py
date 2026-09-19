from pathlib import Path
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ComposeConfigurationTests(unittest.TestCase):
    def test_compose_connects_frontend_backend_and_database(self):
        with (PROJECT_ROOT / "docker-compose.yml").open(encoding="utf-8") as compose_file:
            compose = yaml.safe_load(compose_file)

        services = compose["services"]
        self.assertEqual(set(services), {"db", "backend", "frontend"})
        self.assertEqual(services["db"]["image"], "postgres:16-alpine")
        self.assertEqual(services["backend"]["environment"]["DB_HOST"], "db")
        self.assertIn("db", services["backend"]["depends_on"])
        self.assertIn("backend", services["frontend"]["depends_on"])
        self.assertTrue(any("01_init_db.sql" in item for item in services["db"]["volumes"]))


if __name__ == "__main__":
    unittest.main()
