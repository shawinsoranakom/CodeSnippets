def test_override_settings_reusable_on_enter(self):
        """
        Error is raised correctly when reusing the same override_settings
        instance.
        """

        @override_settings(SETTING_ENTER="ENTER")
        def decorated_function():
            pass

        with self.assertRaises(SettingChangeEnterException):
            decorated_function()
        signals.setting_changed.disconnect(self.receiver)
        # This call shouldn't raise any errors.
        decorated_function()