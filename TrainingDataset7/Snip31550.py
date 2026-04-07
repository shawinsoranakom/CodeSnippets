def test_for_update_requires_transaction(self):
        """
        A TransactionManagementError is raised
        when a select_for_update query is executed outside of a transaction.
        """
        msg = "select_for_update cannot be used outside of a transaction."
        with self.assertRaisesMessage(transaction.TransactionManagementError, msg):
            list(Person.objects.select_for_update())