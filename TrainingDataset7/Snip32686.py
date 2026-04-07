def test_validate_disallowed_async_task(self):
        with mock.patch.multiple(default_task_backend, supports_async_task=False):
            with self.assertRaisesMessage(
                InvalidTask, "Backend does not support async Tasks."
            ):
                default_task_backend.validate_task(test_tasks.noop_task_async)