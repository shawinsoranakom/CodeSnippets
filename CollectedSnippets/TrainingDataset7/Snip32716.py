def test_enqueue_task(self):
        result = test_tasks.noop_task.enqueue()

        self.assertEqual(result.status, TaskResultStatus.READY)
        self.assertEqual(result.task, test_tasks.noop_task)
        self.assertEqual(result.args, [])
        self.assertEqual(result.kwargs, {})

        self.assertEqual(default_task_backend.results, [result])