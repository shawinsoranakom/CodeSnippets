def test_no_enqueue(self):
        with self.assertRaisesMessage(
            TypeError,
            "Can't instantiate abstract class CustomBackendNoEnqueue "
            "without an implementation for abstract method 'enqueue'",
        ):
            test_tasks.noop_task.using(backend="no_enqueue")