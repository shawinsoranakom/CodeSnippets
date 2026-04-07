def test_builtin_with_settings(self):
        """
        alternate: manage.py builtin commands work with settings provided as
        argument
        """
        args = ["check", "--settings=alternate_settings", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertOutput(out, SYSTEM_CHECK_MSG)
        self.assertNoOutput(err)