def test_migration_warning_multiple_apps(self):
        self.runserver_command.check_migrations()
        output = self.stdout.getvalue()
        self.assertIn("You have 2 unapplied migration(s)", output)
        self.assertIn(
            "apply the migrations for app(s): another_app_waiting_migration, "
            "app_waiting_migration.",
            output,
        )