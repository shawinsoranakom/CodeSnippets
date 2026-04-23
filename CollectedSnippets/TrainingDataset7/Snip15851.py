def test_short_option_then_setting(self):
        """Short options passed before settings are correctly handled."""
        args = ["base_command", "testlabel", "-a", "x", "--settings=alternate_settings"]
        self._test(args)