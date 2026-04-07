def test_enqueue_task(self):
        for task in [test_tasks.noop_task, test_tasks.noop_task_async]:
            with self.subTest(task):
                result = cast(Task, task).enqueue(1, two=3)

                self.assertEqual(result.status, TaskResultStatus.READY)
                self.assertIs(result.is_finished, False)
                self.assertIsNone(result.started_at)
                self.assertIsNone(result.last_attempted_at)
                self.assertIsNone(result.finished_at)
                with self.assertRaisesMessage(ValueError, "Task has not finished yet"):
                    result.return_value
                self.assertEqual(result.task, task)
                self.assertEqual(result.args, [1])
                self.assertEqual(result.kwargs, {"two": 3})
                self.assertEqual(result.attempts, 0)

                self.assertIn(result, default_task_backend.results)