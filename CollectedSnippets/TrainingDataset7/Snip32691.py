async def test_validate_on_aenqueue(self):
        task_with_custom_queue_name = test_tasks.noop_task.using(
            queue_name="unknown_queue"
        )

        with override_settings(
            TASKS={
                "default": {
                    "BACKEND": "django.tasks.backends.dummy.DummyBackend",
                    "QUEUES": ["queue-1"],
                }
            }
        ):
            with self.assertRaisesMessage(
                InvalidTask, "Queue 'unknown_queue' is not valid for backend"
            ):
                await task_with_custom_queue_name.aenqueue()