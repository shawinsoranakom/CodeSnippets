def test_custom_command_with_settings(self):
        """
        fulldefault: manage.py can execute user commands when settings are
        provided as argument.
        """
        args = ["noargs_command", "--settings=test_project.settings"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")