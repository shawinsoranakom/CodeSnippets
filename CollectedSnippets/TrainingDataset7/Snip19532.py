def test_database_system_checks(self):
        database_check = mock.Mock(return_value=[], tags=[Tags.database])

        with override_system_checks([database_check]):
            call_command("check")
            database_check.assert_not_called()
            call_command("check", databases=["default"])
            database_check.assert_called_once_with(
                app_configs=None, databases=["default"]
            )