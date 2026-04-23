def test_for_update_requires_transaction_only_in_execution(self):
        """
        No TransactionManagementError is raised
        when select_for_update is invoked outside of a transaction -
        only when the query is executed.
        """
        people = Person.objects.select_for_update()
        msg = "select_for_update cannot be used outside of a transaction."
        with self.assertRaisesMessage(transaction.TransactionManagementError, msg):
            list(people)