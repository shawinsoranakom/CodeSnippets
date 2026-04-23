def test_fails_with_keyerror_on_incomplete_config(self):
        with self.assertRaises(KeyError):
            self.settings_to_cmd_args_env({})