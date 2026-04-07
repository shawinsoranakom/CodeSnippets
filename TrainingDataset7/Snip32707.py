def test_successful_task_no_none_in_logs(self):
        with self.assertLogs("django.tasks", level="DEBUG") as captured_logs:
            result = test_tasks.noop_task.enqueue()

        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)

        for log_output in captured_logs.output:
            self.assertNotIn("None", log_output)