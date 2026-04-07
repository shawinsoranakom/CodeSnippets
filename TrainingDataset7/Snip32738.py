def test_get_incorrect_result(self):
        result = default_task_backend.enqueue(test_tasks.noop_task_async, (), {})
        with self.assertRaisesMessage(TaskResultMismatch, "Task does not match"):
            test_tasks.noop_task.get_result(result.id)