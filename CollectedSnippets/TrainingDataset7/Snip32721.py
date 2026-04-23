def test_using_queue_name(self):
        self.assertEqual(test_tasks.noop_task.queue_name, DEFAULT_TASK_QUEUE_NAME)
        self.assertEqual(
            test_tasks.noop_task.using(queue_name="queue_1").queue_name, "queue_1"
        )
        self.assertEqual(test_tasks.noop_task.queue_name, DEFAULT_TASK_QUEUE_NAME)