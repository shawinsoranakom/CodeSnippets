async def test_result_async(self):
        result = await default_task_backend.aenqueue(
            test_tasks.calculate_meaning_of_life, [], {}
        )

        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)
        self.assertEqual(result.return_value, 42)