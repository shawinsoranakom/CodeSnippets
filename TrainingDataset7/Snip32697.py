def test_throws_keyboard_interrupt(self):
        with self.assertRaises(KeyboardInterrupt):
            with self.assertNoLogs("django.tasks", level="ERROR"):
                default_task_backend.enqueue(
                    test_tasks.failing_task_keyboard_interrupt, [], {}
                )