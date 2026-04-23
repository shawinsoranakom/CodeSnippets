def test_database_operations_init(self):
        """
        DatabaseOperations initialization doesn't query the database.
        See #17656.
        """
        with self.assertNumQueries(0):
            connection.ops.__class__(connection)