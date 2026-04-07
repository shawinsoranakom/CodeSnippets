def test_disallowed_database_queries(self):
        message = (
            "Database queries to 'other' are not allowed in this test. "
            "Add 'other' to test_utils.test_transactiontestcase."
            "DisallowedDatabaseQueriesTests.databases to ensure proper test "
            "isolation and silence this failure."
        )
        with self.assertRaisesMessage(DatabaseOperationForbidden, message):
            Car.objects.using("other").get()