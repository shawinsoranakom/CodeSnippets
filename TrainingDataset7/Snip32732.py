async def test_call_task_async(self):
        self.assertEqual(await test_tasks.calculate_meaning_of_life.acall(), 42)