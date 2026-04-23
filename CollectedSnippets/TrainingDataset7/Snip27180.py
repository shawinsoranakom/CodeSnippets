def test_makemigrations_custom_autodetector(self):
        class CustomAutodetector(MigrationAutodetector):
            def changes(self, *args, **kwargs):
                return []

        class CustomMakeMigrationsCommand(MakeMigrationsCommand):
            autodetector = CustomAutodetector

        class NewModel(models.Model):
            class Meta:
                app_label = "migrated_app"

        out = io.StringIO()
        command = CustomMakeMigrationsCommand(stdout=out)
        call_command(command, "migrated_app", stdout=out)
        self.assertIn("No changes detected", out.getvalue())