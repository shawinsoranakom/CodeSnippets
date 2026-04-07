async def test_refresh_result(self):
        result = await test_tasks.noop_task.aenqueue()

        original_result = dataclasses.asdict(result)

        result.refresh()

        self.assertEqual(dataclasses.asdict(result), original_result)

        await result.arefresh()

        self.assertEqual(dataclasses.asdict(result), original_result)