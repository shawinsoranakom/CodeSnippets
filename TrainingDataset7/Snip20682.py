def test_options_non_deprecated_keys_preferred(self):
        expected_args = [
            "mysql",
            "--user=someuser",
            "--host=somehost",
            "--port=444",
            "optiondbname",
        ]
        expected_env = {"MYSQL_PWD": "optionpassword"}
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "settingdbname",
                    "USER": "someuser",
                    "PASSWORD": "settingpassword",
                    "HOST": "somehost",
                    "PORT": 444,
                    "OPTIONS": {
                        "database": "optiondbname",
                        "db": "deprecatedoptiondbname",
                        "password": "optionpassword",
                        "passwd": "deprecatedoptionpassword",
                    },
                }
            ),
            (expected_args, expected_env),
        )