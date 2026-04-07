def test_app_command_multiple_apps(self):
        "User AppCommands raise an error when multiple app names are provided"
        args = ["app_command", "auth", "contenttypes"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE:AppCommand name=django.contrib.auth, options=")
        self.assertOutput(
            out,
            ", options=[('force_color', False), ('no_color', False), "
            "('pythonpath', None), ('settings', None), ('traceback', False), "
            "('verbosity', 1)]",
        )
        self.assertOutput(
            out, "EXECUTE:AppCommand name=django.contrib.contenttypes, options="
        )
        self.assertOutput(
            out,
            ", options=[('force_color', False), ('no_color', False), "
            "('pythonpath', None), ('settings', None), ('traceback', False), "
            "('verbosity', 1)]",
        )