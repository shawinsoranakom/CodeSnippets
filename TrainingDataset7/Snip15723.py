def test_builtin_with_settings(self):
        """
        default: manage.py builtin commands succeed if settings are provided as
        argument.
        """
        args = ["check", "--settings=test_project.settings", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)