def test_base_command_with_wrong_option(self):
        """
        User BaseCommands outputs command usage when wrong option is specified
        """
        args = ["base_command", "--invalid"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "usage: manage.py base_command")
        self.assertOutput(err, "error: unrecognized arguments: --invalid")