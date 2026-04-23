def test_override_settings_exit(self):
        """Receiver fails on exit only."""
        with self.assertRaises(SettingChangeExitException):
            with override_settings(SETTING_PASS="EXIT", SETTING_EXIT="EXIT"):
                pass

        self.check_settings()
        # Two settings were touched, so expect two calls of `spy_receiver`.
        self.check_spy_receiver_exit_calls(call_count=2)