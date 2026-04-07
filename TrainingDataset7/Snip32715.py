def test_task_decorator(self):
        self.assertIsInstance(test_tasks.noop_task, Task)
        self.assertIsInstance(test_tasks.noop_task_async, Task)
        self.assertIsInstance(test_tasks.noop_task_from_bare_decorator, Task)