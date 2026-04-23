async def test_get_missing_result(self):
        with self.assertRaises(TaskResultDoesNotExist):
            test_tasks.noop_task.get_result("123")

        with self.assertRaises(TaskResultDoesNotExist):
            await test_tasks.noop_task.aget_result("123")