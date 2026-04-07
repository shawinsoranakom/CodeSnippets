def test_context(self):
        result = test_tasks.test_context.enqueue(1)
        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)