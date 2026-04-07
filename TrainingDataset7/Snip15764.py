def test_custom_command(self):
        """
        multiple: manage.py can't execute user commands using default settings
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'noargs_command'")