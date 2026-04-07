def test_refresh_result(self):
        result = default_task_backend.enqueue(
            test_tasks.calculate_meaning_of_life, (), {}
        )

        enqueued_result = default_task_backend.results[0]
        object.__setattr__(enqueued_result, "status", TaskResultStatus.SUCCESSFUL)

        self.assertEqual(result.status, TaskResultStatus.READY)
        result.refresh()
        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)