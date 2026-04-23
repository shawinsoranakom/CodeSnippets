def test_custom_command(self):
        """
        minimal: manage.py can't execute user commands without appropriate
        settings
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'noargs_command'")