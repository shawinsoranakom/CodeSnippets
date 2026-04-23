def test_default_name(self):
        # A test db name isn't set.
        prod_name = "hodor"
        test_connection = get_connection_copy()
        test_connection.settings_dict["NAME"] = prod_name
        test_connection.settings_dict["TEST"] = {"NAME": None}
        signature = BaseDatabaseCreation(test_connection).test_db_signature()
        self.assertEqual(signature[3], TEST_DATABASE_PREFIX + prod_name)