def test_setting_then_short_option(self):
        """Short options passed after settings are correctly handled."""
        args = ["base_command", "testlabel", "--settings=alternate_settings", "-a", "x"]
        self._test(args)