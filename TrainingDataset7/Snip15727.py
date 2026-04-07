def test_custom_command(self):
        """
        default: manage.py can execute user commands when default settings are
        appropriate.
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")