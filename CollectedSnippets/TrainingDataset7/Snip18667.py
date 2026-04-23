def test_service_name(self):
        from django.db.backends.postgresql.base import DatabaseWrapper

        settings = connection.settings_dict.copy()
        settings["OPTIONS"] = {"service": "my_service"}
        settings["NAME"] = ""
        params = DatabaseWrapper(settings).get_connection_params()
        self.assertEqual(params["service"], "my_service")
        self.assertNotIn("database", params)