def test_module_path(self):
        self.assertEqual(test_tasks.noop_task.module_path, "tasks.tasks.noop_task")
        self.assertEqual(
            test_tasks.noop_task_async.module_path, "tasks.tasks.noop_task_async"
        )

        self.assertIs(
            import_string(test_tasks.noop_task.module_path), test_tasks.noop_task
        )
        self.assertIs(
            import_string(test_tasks.noop_task_async.module_path),
            test_tasks.noop_task_async,
        )