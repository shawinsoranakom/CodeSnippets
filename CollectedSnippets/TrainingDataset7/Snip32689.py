def test_clear(self):
        result = test_tasks.noop_task.enqueue()

        default_task_backend.get_result(result.id)

        default_task_backend.clear()

        with self.assertRaisesMessage(TaskResultDoesNotExist, result.id):
            default_task_backend.get_result(result.id)