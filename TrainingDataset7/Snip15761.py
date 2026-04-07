def test_builtin_with_environment(self):
        """
        multiple: manage.py can execute builtin commands if settings are
        provided in the environment.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args, "alternate_settings")
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)