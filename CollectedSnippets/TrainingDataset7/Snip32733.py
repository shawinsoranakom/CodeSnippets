async def test_call_async_task(self):
        self.assertIsNone(await test_tasks.noop_task_async.acall())