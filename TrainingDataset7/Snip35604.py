def test_mark_for_rollback_on_error_in_transaction(self):
        with transaction.atomic(savepoint=False):
            # Swallow the intentional error raised.
            with self.assertRaisesMessage(Exception, "Oops"):
                # Wrap in `mark_for_rollback_on_error` to check if the
                # transaction is marked broken.
                with transaction.mark_for_rollback_on_error():
                    # Ensure that we are still in a good state.
                    self.assertFalse(transaction.get_rollback())

                    raise Exception("Oops")

                # mark_for_rollback_on_error marked the transaction as broken …
                self.assertTrue(transaction.get_rollback())

            # … and further queries fail.
            msg = "You can't execute queries until the end of the 'atomic' block."
            with self.assertRaisesMessage(transaction.TransactionManagementError, msg):
                Reporter.objects.create()

        # Transaction errors are reset at the end of an transaction, so this
        # should just work.
        Reporter.objects.create()