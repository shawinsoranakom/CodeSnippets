def test_builtin_with_environment(self):
        """
        fulldefault: manage.py builtin commands succeed if settings are
        provided in the environment.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)