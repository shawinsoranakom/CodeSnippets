def test_can_connect_using_sockets(self):
        expected_args = [
            "mysql",
            "--user=someuser",
            "--socket=/path/to/mysql.socket.file",
            "somedbname",
        ]
        expected_env = {"MYSQL_PWD": "somepassword"}
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "somedbname",
                    "USER": "someuser",
                    "PASSWORD": "somepassword",
                    "HOST": "/path/to/mysql.socket.file",
                    "PORT": None,
                    "OPTIONS": {},
                }
            ),
            (expected_args, expected_env),
        )