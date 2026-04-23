def test_failure_on_exit_transaction(self):
        with transaction.atomic():
            with self.assertRaises(DatabaseError):
                with transaction.atomic():
                    Reporter.objects.create(last_name="Tintin")
                    self.assertEqual(len(Reporter.objects.all()), 1)
                    # Incorrect savepoint id to provoke a database error.
                    connection.savepoint_ids.append("12")
            with self.assertRaises(transaction.TransactionManagementError):
                len(Reporter.objects.all())
            self.assertIs(connection.needs_rollback, True)
            if connection.savepoint_ids:
                connection.savepoint_ids.pop()
        self.assertSequenceEqual(Reporter.objects.all(), [])