def test_call_async_task_sync(self):
        self.assertIsNone(test_tasks.noop_task_async.call())