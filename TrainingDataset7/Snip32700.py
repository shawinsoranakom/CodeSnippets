def test_result(self):
        result = default_task_backend.enqueue(
            test_tasks.calculate_meaning_of_life, [], {}
        )

        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)
        self.assertEqual(result.return_value, 42)