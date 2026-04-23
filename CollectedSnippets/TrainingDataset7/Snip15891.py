def test_settings_configured(self):
        out, err = self.run_manage(
            ["diffsettings"], manage_py="configured_settings_manage.py"
        )
        self.assertNoOutput(err)
        self.assertOutput(out, "CUSTOM = 1  ###\nDEBUG = True")
        # Attributes from django.conf.UserSettingsHolder don't appear.
        self.assertNotInOutput(out, "default_settings = ")