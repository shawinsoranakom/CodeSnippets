def test_setup_test_database_aliases(self):
        """
        The default database must be the first because data migrations
        use the default alias by default.
        """
        tested_connections = db.ConnectionHandler(
            {
                "other": {
                    "ENGINE": "django.db.backends.dummy",
                    "NAME": "dbname",
                },
                "default": {
                    "ENGINE": "django.db.backends.dummy",
                    "NAME": "dbname",
                },
            }
        )
        with mock.patch("django.test.utils.connections", new=tested_connections):
            test_databases, _ = get_unique_databases_and_mirrors()
            self.assertEqual(
                test_databases,
                {
                    ("", "", "django.db.backends.dummy", "test_dbname"): (
                        "dbname",
                        ["default", "other"],
                    ),
                },
            )