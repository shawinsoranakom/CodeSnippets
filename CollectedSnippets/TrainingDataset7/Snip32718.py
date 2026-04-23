def test_enqueue_with_invalid_argument(self):
        with self.assertRaisesMessage(TypeError, "Unsupported type"):
            test_tasks.noop_task.enqueue(datetime.now())