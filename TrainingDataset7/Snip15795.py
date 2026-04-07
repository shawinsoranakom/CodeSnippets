def test_migration_warning_one_app(self):
        self.runserver_command.check_migrations()
        output = self.stdout.getvalue()
        self.assertIn("You have 1 unapplied migration(s)", output)
        self.assertIn("apply the migrations for app(s): app_waiting_migration.", output)