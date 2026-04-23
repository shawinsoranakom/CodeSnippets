def test_database_name_empty(self):
        from django.db.backends.postgresql.base import DatabaseWrapper

        settings = connection.settings_dict.copy()
        settings["NAME"] = ""
        msg = (
            "settings.DATABASES is improperly configured. Please supply the "
            "NAME or OPTIONS['service'] value."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            DatabaseWrapper(settings).get_connection_params()