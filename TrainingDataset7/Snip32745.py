def test_task_error_invalid_exception(self):
        with self.assertLogs("django.tasks"):
            immediate_task = test_tasks.failing_task_value_error.using(
                backend="immediate"
            ).enqueue()

        self.assertEqual(len(immediate_task.errors), 1)

        object.__setattr__(
            immediate_task.errors[0], "exception_class_path", "subprocess.run"
        )

        with self.assertRaisesMessage(
            ValueError, "'subprocess.run' does not reference a valid exception."
        ):
            immediate_task.errors[0].exception_class