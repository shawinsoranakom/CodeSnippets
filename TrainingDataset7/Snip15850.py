def test_option_then_setting(self):
        """Options passed before settings are correctly handled."""
        args = [
            "base_command",
            "testlabel",
            "--option_a=x",
            "--settings=alternate_settings",
        ]
        self._test(args)