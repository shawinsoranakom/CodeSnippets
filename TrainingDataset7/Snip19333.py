def test_database_checks_called(self, mocked_check):
        check_database_backends()
        self.assertFalse(mocked_check.called)
        check_database_backends(databases=self.databases)
        self.assertTrue(mocked_check.called)