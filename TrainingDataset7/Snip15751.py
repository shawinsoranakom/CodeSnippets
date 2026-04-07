def test_builtin_with_environment(self):
        """
        alternate: manage.py builtin commands work if settings are provided in
        the environment
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args, "alternate_settings")
        self.assertOutput(out, SYSTEM_CHECK_MSG)
        self.assertNoOutput(err)