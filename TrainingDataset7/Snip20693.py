def test_parameters(self):
        expected_args = [
            "sqlplus",
            "-L",
            connection.client.connect_string(connection.settings_dict),
            "-HELP",
        ]
        self.assertEqual(
            self.settings_to_cmd_args_env(
                connection.settings_dict,
                parameters=["-HELP"],
            ),
            (expected_args, None),
        )