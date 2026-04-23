async def test_enqueue_task_async(self):
        for task in [test_tasks.noop_task, test_tasks.noop_task_async]:
            with self.subTest(task):
                result = await task.aenqueue()

                self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)
                self.assertIs(result.is_finished, True)
                self.assertIsNotNone(result.started_at)
                self.assertIsNotNone(result.last_attempted_at)
                self.assertIsNotNone(result.finished_at)
                self.assertGreaterEqual(result.started_at, result.enqueued_at)
                self.assertGreaterEqual(result.finished_at, result.started_at)
                self.assertIsNone(result.return_value)
                self.assertEqual(result.task, task)
                self.assertEqual(result.args, [])
                self.assertEqual(result.kwargs, {})
                self.assertEqual(result.attempts, 1)