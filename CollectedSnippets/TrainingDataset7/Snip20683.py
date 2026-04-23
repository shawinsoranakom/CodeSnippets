def test_options_charset(self):
        expected_args = [
            "mysql",
            "--user=someuser",
            "--host=somehost",
            "--port=444",
            "--default-character-set=utf8mb4",
            "somedbname",
        ]
        expected_env = {"MYSQL_PWD": "somepassword"}
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "somedbname",
                    "USER": "someuser",
                    "PASSWORD": "somepassword",
                    "HOST": "somehost",
                    "PORT": 444,
                    "OPTIONS": {"charset": "utf8mb4"},
                }
            ),
            (expected_args, expected_env),
        )