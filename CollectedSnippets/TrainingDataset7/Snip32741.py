def test_get_backend(self):
        self.assertEqual(test_tasks.noop_task.backend, "default")
        self.assertIsInstance(test_tasks.noop_task.get_backend(), DummyBackend)

        immediate_task = test_tasks.noop_task.using(backend="immediate")
        self.assertEqual(immediate_task.backend, "immediate")
        self.assertIsInstance(immediate_task.get_backend(), ImmediateBackend)