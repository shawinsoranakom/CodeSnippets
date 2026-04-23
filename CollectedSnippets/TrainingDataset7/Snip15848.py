def test_setting_then_option(self):
        """Options passed after settings are correctly handled."""
        args = [
            "base_command",
            "testlabel",
            "--settings=alternate_settings",
            "--option_a=x",
        ]
        self._test(args)