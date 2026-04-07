def test_unknown_queue_name(self):
        with self.assertRaisesMessage(
            InvalidTask, "Queue 'queue-2' is not valid for backend."
        ):
            test_tasks.noop_task.using(queue_name="queue-2")
        # Validation is bypassed when the backend QUEUES is an empty list.
        self.assertEqual(
            test_tasks.noop_task.using(
                queue_name="queue-2", backend="immediate"
            ).queue_name,
            "queue-2",
        )