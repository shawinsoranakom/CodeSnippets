def test_missing_settings_dont_prevent_help(self):
        """
        Even if the STATIC_ROOT setting is not set, one can still call the
        `manage.py help collectstatic` command.
        """
        self.write_settings("settings.py", apps=["django.contrib.staticfiles"])
        out, err = self.run_manage(["help", "collectstatic"])
        self.assertNoOutput(err)