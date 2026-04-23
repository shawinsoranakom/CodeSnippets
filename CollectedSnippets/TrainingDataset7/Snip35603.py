def test_atomic_does_not_leak_savepoints_on_failure(self):
        """#23074 -- Savepoints must be released after rollback."""

        # Expect an error when rolling back a savepoint that doesn't exist.
        # Done outside of the transaction block to ensure proper recovery.
        with self.assertRaises(Error):
            # Start a plain transaction.
            with transaction.atomic():
                # Swallow the intentional error raised in the sub-transaction.
                with self.assertRaisesMessage(Exception, "Oops"):
                    # Start a sub-transaction with a savepoint.
                    with transaction.atomic():
                        sid = connection.savepoint_ids[-1]
                        raise Exception("Oops")

                # This is expected to fail because the savepoint no longer
                # exists.
                connection.savepoint_rollback(sid)