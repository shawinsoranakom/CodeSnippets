def test_app_command_some_invalid_app_labels(self):
        """
        User AppCommands can execute when some of the provided app names are
        invalid
        """
        args = ["app_command", "auth", "NOT_AN_APP"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "No installed app with label 'NOT_AN_APP'.")