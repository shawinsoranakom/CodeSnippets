def test_no_backends(self):
        with self.assertRaises(InvalidTaskBackend):
            test_tasks.noop_task.enqueue()