async def test_cannot_refresh_result(self):
        result = await default_task_backend.aenqueue(
            test_tasks.calculate_meaning_of_life, (), {}
        )

        with self.assertRaisesMessage(
            NotImplementedError,
            "This backend does not support retrieving or refreshing results.",
        ):
            await result.arefresh()

        with self.assertRaisesMessage(
            NotImplementedError,
            "This backend does not support retrieving or refreshing results.",
        ):
            result.refresh()