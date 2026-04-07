def test_compose_sql_when_no_connection(self):
        new_connection = no_pool_connection()
        try:
            self.assertEqual(
                new_connection.ops.compose_sql("SELECT %s", ["test"]),
                "SELECT 'test'",
            )
        finally:
            new_connection.close()