def test_dynamic_settings_configured(self):
        # Custom default settings appear.
        out, err = self.run_manage(
            ["diffsettings"], manage_py="configured_dynamic_settings_manage.py"
        )
        self.assertNoOutput(err)
        self.assertOutput(out, "FOO = 'bar'  ###")