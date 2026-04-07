def test_using_priority(self):
        self.assertEqual(test_tasks.noop_task.priority, 0)
        self.assertEqual(test_tasks.noop_task.using(priority=1).priority, 1)
        self.assertEqual(test_tasks.noop_task.priority, 0)