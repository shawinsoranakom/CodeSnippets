def test_clone_test_db_options_ordering(self):
        creation = DatabaseCreation(connection)
        mock_subprocess_call = mock.MagicMock()
        mock_subprocess_call.returncode = 0
        try:
            saved_settings = connection.settings_dict
            connection.settings_dict = {
                "NAME": "source_db",
                "USER": "",
                "PASSWORD": "",
                "PORT": "",
                "HOST": "",
                "ENGINE": "django.db.backends.mysql",
                "OPTIONS": {
                    "read_default_file": "my.cnf",
                },
            }
            with mock.patch.object(subprocess, "Popen") as mocked_popen:
                mocked_popen.return_value.__enter__.return_value = mock_subprocess_call
                creation._clone_db("source_db", "target_db")
                mocked_popen.assert_has_calls(
                    [
                        mock.call(
                            [
                                "mysqldump",
                                "--defaults-file=my.cnf",
                                "--routines",
                                "--events",
                                "source_db",
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=None,
                        ),
                    ]
                )
        finally:
            connection.settings_dict = saved_settings