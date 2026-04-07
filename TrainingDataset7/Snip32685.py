def test_errors(self):
        result = test_tasks.noop_task.enqueue()
        self.assertEqual(result.errors, [])