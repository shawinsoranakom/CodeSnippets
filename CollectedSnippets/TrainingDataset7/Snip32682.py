async def test_refresh_result_async(self):
        result = await default_task_backend.aenqueue(
            test_tasks.calculate_meaning_of_life, (), {}
        )

        enqueued_result = default_task_backend.results[0]
        object.__setattr__(enqueued_result, "status", TaskResultStatus.SUCCESSFUL)

        self.assertEqual(result.status, TaskResultStatus.READY)
        await result.arefresh()
        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)