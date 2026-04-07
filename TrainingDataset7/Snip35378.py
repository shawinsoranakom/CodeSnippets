def test_disallowed_database_queries(self):
        expected_message = (
            "Database queries to 'default' are not allowed in SimpleTestCase "
            "subclasses. Either subclass TestCase or TransactionTestCase to "
            "ensure proper test isolation or add 'default' to "
            "test_utils.tests.DisallowedDatabaseQueriesTests.databases to "
            "silence this failure."
        )
        with self.assertRaisesMessage(DatabaseOperationForbidden, expected_message):
            Car.objects.first()