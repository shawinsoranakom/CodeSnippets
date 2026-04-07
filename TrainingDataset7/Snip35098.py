def test_serialization(self):
        tested_connections = db.ConnectionHandler(
            {
                "default": {
                    "ENGINE": "django.db.backends.dummy",
                },
            }
        )
        with mock.patch(
            "django.db.backends.dummy.base.DatabaseWrapper.creation_class"
        ) as mocked_db_creation:
            with mock.patch("django.test.utils.connections", new=tested_connections):
                self.runner_instance.setup_databases()
        mocked_db_creation.return_value.create_test_db.assert_called_once_with(
            verbosity=0, autoclobber=False, keepdb=False
        )
        mocked_db_creation.return_value.serialize_db_to_string.assert_called_once_with()