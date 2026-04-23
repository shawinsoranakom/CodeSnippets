def test_app_command_invalid_app_label(self):
        "User AppCommands can execute when a single app name is provided"
        args = ["app_command", "NOT_AN_APP"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "No installed app with label 'NOT_AN_APP'.")