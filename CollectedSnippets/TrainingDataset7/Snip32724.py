def test_using_missing_backend(self):
        self.assertEqual(test_tasks.noop_task.backend, "default")

        with self.assertRaisesMessage(
            InvalidTaskBackend,
            "Could not find backend 'does.not.exist': No module named 'does'",
        ):
            test_tasks.noop_task.using(backend="missing")