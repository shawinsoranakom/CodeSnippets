def test_options(self):
        with self.assertLogs(__name__, level="INFO") as captured_logs:
            test_tasks.noop_task.enqueue()
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("PREFIX: Task enqueued", captured_logs.output[0])