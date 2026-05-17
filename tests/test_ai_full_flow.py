import unittest

from ai_engine.schemas import LogContext, NormalizedLog
from ai_engine.service import AIAnalysisService


class FakeCursor:
    def __init__(self, connection, dictionary=False):
        self.connection = connection
        self.dictionary = dictionary
        self.lastrowid = None
        self._result = None

    def execute(self, query, params=None):
        normalized_query = " ".join(query.lower().split())

        if normalized_query.startswith("insert into logs"):
            self.connection.log_id += 1
            self.lastrowid = self.connection.log_id
            self.connection.logs.append({"id": self.lastrowid, "params": params})
            return

        if normalized_query.startswith("insert into ai_log_analysis"):
            self.connection.ai_rows.append({"params": params})
            return

        if "count(*) as total" in normalized_query and "from logs" in normalized_query:
            if "level='error'" in normalized_query:
                self._result = {"total": 26}
            elif "level='warning'" in normalized_query:
                self._result = {"total": 8}
            else:
                self._result = {"total": 40}
            return

        raise AssertionError(f"Unexpected query: {query}")

    def fetchone(self):
        return self._result

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.log_id = 0
        self.logs = []
        self.ai_rows = []
        self.commits = 0

    def cursor(self, dictionary=False):
        return FakeCursor(self, dictionary=dictionary)

    def commit(self):
        self.commits += 1

    def close(self):
        pass


class AIFullFlowTest(unittest.TestCase):
    def test_ai_service_classifies_and_flags_spike(self):
        service = AIAnalysisService()
        result = service.analyze_log(
            NormalizedLog(
                level="ERROR",
                message="Payment gateway timeout while processing transaction",
                service_name="banking-system",
            ),
            LogContext(error_count=26, warning_count=8, service_log_count=40),
        )

        self.assertEqual(result.predicted_category, "PAYMENT_ERROR")
        self.assertEqual(result.predicted_severity, "HIGH")
        self.assertIsInstance(result.is_anomaly, bool)
        self.assertIsNotNone(result.anomaly_score)
        self.assertIn("banking-system", result.insight)

    def test_existing_logs_endpoint_runs_ai_flow_without_agent_changes(self):
        import main

        fake_connection = FakeConnection()
        original_get_connection = main.get_connection
        main.get_connection = lambda: fake_connection

        try:
            response = main.add_log(
                main.LogIn(
                    level="ERROR",
                    message="Database connection timeout",
                    service_name="banking-system",
                ),
                agent={"agent_id": "agent-1", "service_name": "banking-system"},
            )
        finally:
            main.get_connection = original_get_connection

        self.assertEqual(response["message"], "Log stored successfully")
        self.assertEqual(response["level"], "ERROR")
        self.assertIn("ai_analysis", response)
        self.assertEqual(response["ai_analysis"]["predicted_category"], "DATABASE_ERROR")
        self.assertEqual(len(fake_connection.logs), 1)
        self.assertEqual(len(fake_connection.ai_rows), 1)


if __name__ == "__main__":
    unittest.main()
