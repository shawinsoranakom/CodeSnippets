def test_max_query_params_respects_variable_limit(self):
        limit_name = sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER
        current_limit = connection.features.max_query_params
        new_limit = min(42, current_limit)
        try:
            connection.connection.setlimit(limit_name, new_limit)
            self.assertEqual(connection.features.max_query_params, new_limit)
        finally:
            connection.connection.setlimit(limit_name, current_limit)
        self.assertEqual(connection.features.max_query_params, current_limit)