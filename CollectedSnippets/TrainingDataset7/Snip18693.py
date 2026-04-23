def test_get_database_version(self):
        new_connection = no_pool_connection()
        new_connection.pg_version = 150009
        self.assertEqual(new_connection.get_database_version(), (15, 9))