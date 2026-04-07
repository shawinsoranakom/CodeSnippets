def test_disallowed_database_connections(self):
        expected_message = (
            "Database connections to 'default' are not allowed in SimpleTestCase "
            "subclasses. Either subclass TestCase or TransactionTestCase to "
            "ensure proper test isolation or add 'default' to "
            "test_utils.tests.DisallowedDatabaseQueriesTests.databases to "
            "silence this failure."
        )
        with self.assertRaisesMessage(DatabaseOperationForbidden, expected_message):
            connection.connect()
        with self.assertRaisesMessage(DatabaseOperationForbidden, expected_message):
            connection.temporary_connection()