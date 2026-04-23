def test_empty_default_database(self):
        """
        An empty default database in settings does not raise an
        ImproperlyConfigured error when running a unit test that does not use a
        database.
        """
        tested_connections = db.ConnectionHandler({"default": {}})
        with mock.patch("django.db.connections", new=tested_connections):
            connection = tested_connections[db.utils.DEFAULT_DB_ALIAS]
            self.assertEqual(
                connection.settings_dict["ENGINE"], "django.db.backends.dummy"
            )
            connections_support_transactions()