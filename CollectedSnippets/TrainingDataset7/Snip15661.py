def test_commands_with_invalid_settings(self):
        """
        Commands that don't require settings succeed if the settings file
        doesn't exist.
        """
        args = ["startproject"]
        out, err = self.run_django_admin(args, settings_file="bad_settings")
        self.assertNoOutput(out)
        self.assertOutput(err, "You must provide a project name", regex=True)