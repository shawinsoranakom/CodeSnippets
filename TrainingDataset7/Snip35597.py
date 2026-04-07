def test_atomic_prevents_calling_transaction_methods(self):
        with transaction.atomic():
            with self.assertRaisesMessage(
                transaction.TransactionManagementError, self.forbidden_atomic_msg
            ):
                transaction.commit()
            with self.assertRaisesMessage(
                transaction.TransactionManagementError, self.forbidden_atomic_msg
            ):
                transaction.rollback()