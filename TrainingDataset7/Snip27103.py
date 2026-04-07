def test_makemigrations_model_rename_interactive(self, mock_input):
        class RenamedModel(models.Model):
            silly_field = models.BooleanField(default=False)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(
            module="migrations.test_migrations_no_default",
        ):
            with captured_stdout() as out:
                call_command("makemigrations", "migrations", interactive=True)
        self.assertIn("Rename model SillyModel to RenamedModel", out.getvalue())