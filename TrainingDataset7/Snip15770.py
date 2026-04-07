def test_key_error(self):
        self.write_settings("settings.py", sdict={"BAD_VAR": 'DATABASES["blah"]'})
        args = ["collectstatic", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "KeyError: 'blah'")