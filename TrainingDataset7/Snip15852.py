def test_option_then_setting_then_option(self):
        """Options are correctly handled when they are passed before and after
        a setting."""
        args = [
            "base_command",
            "testlabel",
            "--option_a=x",
            "--settings=alternate_settings",
            "--option_b=y",
        ]
        self._test(args, option_b="'y'")