async def test_get_missing_result(self):
        with self.assertRaises(TaskResultDoesNotExist):
            default_task_backend.get_result("123")

        with self.assertRaises(TaskResultDoesNotExist):
            await default_task_backend.aget_result("123")