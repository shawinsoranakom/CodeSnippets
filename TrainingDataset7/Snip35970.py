def test_disallowed_abbreviated_options(self):
        """
        To avoid conflicts with custom options, commands don't allow
        abbreviated forms of the --setting and --pythonpath options.
        """
        self.write_settings("settings.py", apps=["user_commands"])
        out, err = self.run_manage(["set_option", "--set", "foo"])
        self.assertNoOutput(err)
        self.assertEqual(out.strip(), "Set foo")