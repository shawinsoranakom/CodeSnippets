def test_takes_context(self):
        result = test_tasks.get_task_id.enqueue()
        self.assertEqual(result.status, TaskResultStatus.READY)