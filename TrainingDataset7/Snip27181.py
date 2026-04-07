def test_migrate_custom_autodetector(self):
        class CustomAutodetector(MigrationAutodetector):
            def changes(self, *args, **kwargs):
                return []

        class CustomMigrateCommand(MigrateCommand):
            autodetector = CustomAutodetector

        class NewModel(models.Model):
            class Meta:
                app_label = "migrated_app"

        out = io.StringIO()
        command = CustomMigrateCommand(stdout=out)

        out = io.StringIO()
        try:
            call_command(command, verbosity=0)
            call_command(command, stdout=out, no_color=True)
            command_stdout = out.getvalue().lower()
            self.assertEqual(
                "operations to perform:\n"
                "  apply all migrations: migrated_app\n"
                "running migrations:\n"
                "  no migrations to apply.\n",
                command_stdout,
            )
        finally:
            call_command(command, "migrated_app", "zero", verbosity=0)