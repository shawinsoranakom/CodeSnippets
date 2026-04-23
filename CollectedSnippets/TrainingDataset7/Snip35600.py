def test_atomic_prevents_queries_in_broken_transaction_after_client_close(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Archibald", last_name="Haddock")
            connection.close()
            # The connection is closed and the transaction is marked as
            # needing rollback. This will raise an InterfaceError on databases
            # that refuse to create cursors on closed connections (PostgreSQL)
            # and a TransactionManagementError on other databases.
            with self.assertRaises(Error):
                Reporter.objects.create(first_name="Cuthbert", last_name="Calculus")
        # The connection is usable again .
        self.assertEqual(Reporter.objects.count(), 0)