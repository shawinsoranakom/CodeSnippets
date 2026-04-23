def test_auto_is_null_auto_config(self):
        query = "set sql_auto_is_null = 0"
        connection.init_connection_state()
        last_query = connection.queries[-1]["sql"].lower()
        if connection.features.is_sql_auto_is_null_enabled:
            self.assertIn(query, last_query)
        else:
            self.assertNotIn(query, last_query)