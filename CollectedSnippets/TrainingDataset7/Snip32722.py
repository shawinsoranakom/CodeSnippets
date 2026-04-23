def test_using_run_after(self):
        now = timezone.now()

        self.assertIsNone(test_tasks.noop_task.run_after)
        self.assertEqual(test_tasks.noop_task.using(run_after=now).run_after, now)
        self.assertIsNone(test_tasks.noop_task.run_after)