def test_pooling_health_checks(self):
        new_connection = no_pool_connection(alias="default_pool")
        new_connection.settings_dict["OPTIONS"]["pool"] = True
        new_connection.settings_dict["CONN_HEALTH_CHECKS"] = False

        try:
            self.assertIsNone(new_connection.pool._check)
        finally:
            new_connection.close_pool()

        new_connection.settings_dict["CONN_HEALTH_CHECKS"] = True
        try:
            self.assertIsNotNone(new_connection.pool._check)
        finally:
            new_connection.close_pool()