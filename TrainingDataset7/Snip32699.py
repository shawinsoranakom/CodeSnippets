def test_complex_return_value(self):
        with self.assertLogs("django.tasks", level="ERROR"):
            result = test_tasks.complex_return_value.enqueue()

        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.last_attempted_at)
        self.assertIsNotNone(result.finished_at)
        self.assertGreaterEqual(result.started_at, result.enqueued_at)
        self.assertGreaterEqual(result.finished_at, result.started_at)
        self.assertIsNone(result._return_value)
        self.assertEqual(result.errors[0].exception_class, TypeError)
        self.assertIn("Unsupported type", result.errors[0].traceback)