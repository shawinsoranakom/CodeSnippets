def test_backend_does_not_support_priority(self):
        with self.assertRaisesMessage(
            InvalidTask, "Backend does not support setting priority of tasks."
        ):
            test_tasks.noop_task.using(priority=10)