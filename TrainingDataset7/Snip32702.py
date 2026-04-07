async def test_cannot_get_result(self):
        with self.assertRaisesMessage(
            NotImplementedError,
            "This backend does not support retrieving or refreshing results.",
        ):
            default_task_backend.get_result("123")

        with self.assertRaisesMessage(
            NotImplementedError,
            "This backend does not support retrieving or refreshing results.",
        ):
            await default_task_backend.aget_result(123)