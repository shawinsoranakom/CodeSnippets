def test_last_executed_query_base_fallback(self):
        sql = "INVALID SQL"
        params = []
        with connection.cursor() as cursor:
            cursor.close()
            try:
                cursor.execute(sql, params)
            except connection.features.closed_cursor_error_class:
                pass
            self.assertIsNotNone(
                connection.ops.last_executed_query(cursor, sql, params),
            )