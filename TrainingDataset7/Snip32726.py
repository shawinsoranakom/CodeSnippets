def test_chained_using(self):
        now = timezone.now()

        run_after_task = test_tasks.noop_task.using(run_after=now)
        self.assertEqual(run_after_task.run_after, now)

        priority_task = run_after_task.using(priority=10)
        self.assertEqual(priority_task.priority, 10)
        self.assertEqual(priority_task.run_after, now)

        self.assertEqual(run_after_task.priority, 0)