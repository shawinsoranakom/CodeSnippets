def test_failed_logs(self):
        with self.assertLogs("django.tasks", level="DEBUG") as captured_logs:
            result = test_tasks.failing_task_value_error.enqueue()

        self.assertEqual(len(captured_logs.output), 3)
        self.assertIn("state=RUNNING", captured_logs.output[1])
        self.assertIn(result.id, captured_logs.output[1])

        self.assertIn("state=FAILED", captured_logs.output[2])
        self.assertIn(result.id, captured_logs.output[2])