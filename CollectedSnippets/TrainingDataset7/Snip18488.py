def test_custom_test_name(self):
        # A regular test db name is set.
        test_name = "hodor"
        test_connection = get_connection_copy()
        test_connection.settings_dict["TEST"] = {"NAME": test_name}
        signature = BaseDatabaseCreation(test_connection).test_db_signature()
        self.assertEqual(signature[3], test_name)