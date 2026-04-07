def test_builtin_command(self):
        """
        default: manage.py builtin commands succeed when default settings are
        appropriate.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)