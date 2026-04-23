def test_custom_command_with_environment(self):
        """
        fulldefault: manage.py can execute user commands when settings are
        provided in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")