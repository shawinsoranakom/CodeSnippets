async def test_aenqueue_with_invalid_argument(self):
        with self.assertRaisesMessage(TypeError, "Unsupported type"):
            await test_tasks.noop_task.aenqueue(datetime.now())