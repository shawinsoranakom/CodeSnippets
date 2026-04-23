def test_mark_for_rollback_on_error_in_autocommit(self):
        self.assertTrue(transaction.get_autocommit())

        # Swallow the intentional error raised.
        with self.assertRaisesMessage(Exception, "Oops"):
            # Wrap in `mark_for_rollback_on_error` to check if the transaction
            # is marked broken.
            with transaction.mark_for_rollback_on_error():
                # Ensure that we are still in a good state.
                self.assertFalse(transaction.get_connection().needs_rollback)

                raise Exception("Oops")

            # Ensure that `mark_for_rollback_on_error` did not mark the
            # transaction as broken, since we are in autocommit mode …
            self.assertFalse(transaction.get_connection().needs_rollback)

        # … and further queries work nicely.
        Reporter.objects.create()