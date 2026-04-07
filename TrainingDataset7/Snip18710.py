def test_max_query_params_without_established_connection(self):
        new_connection = connection.copy()
        new_connection.settings_dict = copy.deepcopy(connection.settings_dict)
        self.assertIsNone(new_connection.connection)
        try:
            result = new_connection.features.max_query_params
            self.assertIsInstance(result, int)
        finally:
            new_connection._close()