def test_custom_test_name(self):
        test_connection = copy.copy(connections[DEFAULT_DB_ALIAS])
        test_connection.settings_dict = copy.deepcopy(
            connections[DEFAULT_DB_ALIAS].settings_dict
        )
        test_connection.settings_dict["NAME"] = None
        test_connection.settings_dict["TEST"]["NAME"] = "custom.sqlite.db"
        signature = test_connection.creation_class(test_connection).test_db_signature()
        self.assertEqual(signature, (None, "custom.sqlite.db"))