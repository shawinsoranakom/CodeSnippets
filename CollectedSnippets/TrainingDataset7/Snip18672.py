def test_connect_pool_set_to_true(self):
        new_connection = no_pool_connection(alias="default_pool")
        new_connection.settings_dict["OPTIONS"]["pool"] = True
        try:
            self.assertIsNotNone(new_connection.pool)
        finally:
            new_connection.close_pool()