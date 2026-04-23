async def test_enqueue_task_async(self):
        result = await test_tasks.noop_task.aenqueue()

        self.assertEqual(result.status, TaskResultStatus.READY)
        self.assertEqual(result.task, test_tasks.noop_task)
        self.assertEqual(result.args, [])
        self.assertEqual(result.kwargs, {})

        self.assertEqual(default_task_backend.results, [result])