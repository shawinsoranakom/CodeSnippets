def test_override_settings_both(self):
        """Receiver fails on both enter and exit."""
        with self.assertRaises(SettingChangeEnterException):
            with override_settings(SETTING_PASS="BOTH", SETTING_BOTH="BOTH"):
                pass

        self.check_settings()
        # Two settings were touched, so expect two calls of `spy_receiver`.
        self.check_spy_receiver_exit_calls(call_count=2)