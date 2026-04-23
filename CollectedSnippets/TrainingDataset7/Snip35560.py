def test_raises_exception_non_autocommit_mode(self):
        def should_never_be_called():
            raise AssertionError("this function should never be called")

        try:
            connection.set_autocommit(False)
            msg = "on_commit() cannot be used in manual transaction management"
            with self.assertRaisesMessage(transaction.TransactionManagementError, msg):
                transaction.on_commit(should_never_be_called)
        finally:
            connection.set_autocommit(True)