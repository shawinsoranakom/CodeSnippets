def test_disallowed_database_connection(self):
        message = (
            "Database connections to 'other' are not allowed in this test. "
            "Add 'other' to test_utils.test_testcase.TestTestCase.databases to "
            "ensure proper test isolation and silence this failure."
        )
        with self.assertRaisesMessage(DatabaseOperationForbidden, message):
            connections["other"].connect()
        with self.assertRaisesMessage(DatabaseOperationForbidden, message):
            connections["other"].temporary_connection()