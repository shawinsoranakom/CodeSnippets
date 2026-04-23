def test_service_name_default_db(self):
        # None is used to connect to the default 'postgres' db.
        from django.db.backends.postgresql.base import DatabaseWrapper

        settings = connection.settings_dict.copy()
        settings["NAME"] = None
        settings["OPTIONS"] = {"service": "django_test"}
        params = DatabaseWrapper(settings).get_connection_params()
        self.assertEqual(params["dbname"], "postgres")
        self.assertNotIn("service", params)