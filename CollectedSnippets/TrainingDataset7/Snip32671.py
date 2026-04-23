def test_enqueue_async_task_on_non_async_backend(self):
        with self.assertRaisesMessage(
            InvalidTask, "Backend does not support async Tasks."
        ):
            default_task_backend.validate_task(test_tasks.noop_task_async)