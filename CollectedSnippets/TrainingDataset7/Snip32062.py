def test_override_settings_enter(self):
        """Receiver fails on enter only."""
        with self.assertRaises(SettingChangeEnterException):
            with override_settings(SETTING_PASS="ENTER", SETTING_ENTER="ENTER"):
                pass

        self.check_settings()
        # Two settings were touched, so expect two calls of `spy_receiver`.
        self.check_spy_receiver_exit_calls(call_count=2)