def test_builtin_command(self):
        """
        alternate: manage.py builtin commands fail with an error when no
        default settings provided.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(
            err, r"No module named '?(test_project\.)?settings'?", regex=True
        )