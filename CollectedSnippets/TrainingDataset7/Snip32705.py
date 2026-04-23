def test_enqueue_logs(self):
        with self.assertLogs("django.tasks", level="DEBUG") as captured_logs:
            result = test_tasks.noop_task.enqueue()

        self.assertEqual(len(captured_logs.output), 3)

        self.assertIn("enqueued", captured_logs.output[0])
        self.assertIn(result.id, captured_logs.output[0])

        self.assertIn("state=RUNNING", captured_logs.output[1])
        self.assertIn(result.id, captured_logs.output[1])

        self.assertIn("state=SUCCESSFUL", captured_logs.output[2])
        self.assertIn(result.id, captured_logs.output[2])