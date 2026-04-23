def test_naive_datetime(self):
        with self.assertRaisesMessage(
            InvalidTask, "run_after must be an aware datetime."
        ):
            test_tasks.noop_task.using(run_after=datetime.now())