def test_using_unknown_backend(self):
        self.assertEqual(test_tasks.noop_task.backend, "default")

        with self.assertRaisesMessage(
            InvalidTaskBackend, "The connection 'unknown' doesn't exist."
        ):
            test_tasks.noop_task.using(backend="unknown")