def test_attribute_error(self):
        """
        manage.py builtin commands does not swallow attribute error due to bad
        settings (#18845).
        """
        self.write_settings("settings.py", sdict={"BAD_VAR": "INSTALLED_APPS.crash"})
        args = ["collectstatic", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "AttributeError: 'list' object has no attribute 'crash'")