def test_doesnt_wait_until_transaction_commit_by_default(self):
        with transaction.atomic():
            result = test_tasks.noop_task.enqueue()

            self.assertIsNotNone(result.enqueued_at)

            self.assertEqual(len(default_task_backend.results), 1)

        self.assertEqual(len(default_task_backend.results), 1)