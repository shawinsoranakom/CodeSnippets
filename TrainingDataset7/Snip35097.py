def test_destroy_test_db_restores_db_name(self):
        tested_connections = db.ConnectionHandler(
            {
                "default": {
                    "ENGINE": settings.DATABASES[db.DEFAULT_DB_ALIAS]["ENGINE"],
                    "NAME": "xxx_test_database",
                },
            }
        )
        # Using the real current name as old_name to not mess with the test
        # suite.
        old_name = settings.DATABASES[db.DEFAULT_DB_ALIAS]["NAME"]
        with mock.patch("django.db.connections", new=tested_connections):
            tested_connections["default"].creation.destroy_test_db(
                old_name, verbosity=0, keepdb=True
            )
            self.assertEqual(
                tested_connections["default"].settings_dict["NAME"], old_name
            )