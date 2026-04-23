def test_custom_default(self):
        """
        The --default option specifies an alternate settings module for
        comparison.
        """
        self.write_settings(
            "settings_default.py", sdict={"FOO": '"foo"', "BAR": '"bar1"'}
        )
        self.write_settings(
            "settings_to_diff.py", sdict={"FOO": '"foo"', "BAR": '"bar2"'}
        )
        out, err = self.run_manage(
            [
                "diffsettings",
                "--settings=settings_to_diff",
                "--default=settings_default",
            ]
        )
        self.assertNoOutput(err)
        self.assertNotInOutput(out, "FOO")
        self.assertOutput(out, "BAR = 'bar2'")