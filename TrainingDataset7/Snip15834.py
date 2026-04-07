def test_app_command_no_apps(self):
        "User AppCommands raise an error when no app name is provided"
        args = ["app_command"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "error: Enter at least one application label.")