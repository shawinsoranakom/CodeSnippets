def test_allowed_database_copy_queries(self):
        new_connection = connection.copy("dynamic_connection")
        try:
            with new_connection.cursor() as cursor:
                sql = f"SELECT 1{new_connection.features.bare_select_suffix}"
                cursor.execute(sql)
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            new_connection.validate_thread_sharing()
            new_connection._close()
            if hasattr(new_connection, "close_pool"):
                new_connection.close_pool()