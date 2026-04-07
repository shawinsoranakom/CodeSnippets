def test_using_correct_backend(self):
        self.assertEqual(default_task_backend, task_backends["default"])
        self.assertIsInstance(task_backends["default"], DummyBackend)