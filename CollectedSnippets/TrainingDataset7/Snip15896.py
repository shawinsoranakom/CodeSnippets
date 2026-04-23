def test_unified_all(self):
        """
        --output=unified --all emits settings diff in unified mode and includes
        settings with the default value.
        """
        self.write_settings("settings_to_diff.py", sdict={"FOO": '"bar"'})
        args = [
            "diffsettings",
            "--settings=settings_to_diff",
            "--output=unified",
            "--all",
        ]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "  APPEND_SLASH = True")
        self.assertOutput(out, "+ FOO = 'bar'")
        self.assertOutput(out, "- SECRET_KEY = ''")