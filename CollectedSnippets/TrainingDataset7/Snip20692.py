def test_with_rlwrap(self):
        expected_args = [
            "/usr/bin/rlwrap",
            "sqlplus",
            "-L",
            connection.client.connect_string(connection.settings_dict),
        ]
        self.assertEqual(
            self.settings_to_cmd_args_env(connection.settings_dict, rlwrap=True),
            (expected_args, None),
        )