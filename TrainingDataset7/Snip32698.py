def test_complex_exception(self):
        with self.assertLogs("django.tasks", level="ERROR"):
            result = test_tasks.complex_exception.enqueue()

        self.assertEqual(result.status, TaskResultStatus.FAILED)
        with self.assertRaisesMessage(ValueError, "Task failed"):
            result.return_value
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.last_attempted_at)
        self.assertIsNotNone(result.finished_at)
        self.assertGreaterEqual(result.started_at, result.enqueued_at)
        self.assertGreaterEqual(result.finished_at, result.started_at)

        self.assertIsNone(result._return_value)
        self.assertEqual(result.errors[0].exception_class, ValueError)
        self.assertIn(
            'ValueError(ValueError("This task failed"))', result.errors[0].traceback
        )

        self.assertEqual(result.task, test_tasks.complex_exception)
        self.assertEqual(result.args, [])
        self.assertEqual(result.kwargs, {})