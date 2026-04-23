def test_database_operations_helper_class(self):
        # Ticket #13630
        self.assertTrue(hasattr(connection, "ops"))
        self.assertTrue(hasattr(connection.ops, "connection"))
        self.assertEqual(connection, connection.ops.connection)