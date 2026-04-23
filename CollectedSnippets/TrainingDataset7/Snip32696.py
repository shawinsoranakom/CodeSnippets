def test_catches_exception(self):
        test_data = [
            (
                test_tasks.failing_task_value_error,  # Task function.
                ValueError,  # Expected exception.
                "This Task failed due to ValueError",  # Expected message.
            ),
            (
                test_tasks.failing_task_system_exit,
                SystemExit,
                "This Task failed due to SystemExit",
            ),
        ]
        for task, exception, message in test_data:
            with (
                self.subTest(task),
                self.assertLogs("django.tasks", level="ERROR") as captured_logs,
            ):
                result = task.enqueue()

                self.assertEqual(len(captured_logs.output), 1)
                self.assertIn(message, captured_logs.output[0])

                self.assertEqual(result.status, TaskResultStatus.FAILED)
                with self.assertRaisesMessage(ValueError, "Task failed"):
                    result.return_value
                self.assertIs(result.is_finished, True)
                self.assertIsNotNone(result.started_at)
                self.assertIsNotNone(result.last_attempted_at)
                self.assertIsNotNone(result.finished_at)
                self.assertGreaterEqual(result.started_at, result.enqueued_at)
                self.assertGreaterEqual(result.finished_at, result.started_at)
                self.assertEqual(result.errors[0].exception_class, exception)
                traceback = result.errors[0].traceback
                self.assertIs(
                    traceback
                    and traceback.endswith(f"{exception.__name__}: {message}\n"),
                    True,
                    traceback,
                )
                self.assertEqual(result.task, task)
                self.assertEqual(result.args, [])
                self.assertEqual(result.kwargs, {})