def test_settings_to_cmd_args_env(self):
        msg = (
            "subclasses of BaseDatabaseClient must provide a "
            "settings_to_cmd_args_env() method or override a runshell()."
        )
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.client.settings_to_cmd_args_env(None, None)