def test_using_creates_new_instance(self):
        new_task = test_tasks.noop_task.using()

        self.assertEqual(new_task, test_tasks.noop_task)
        self.assertIsNot(new_task, test_tasks.noop_task)