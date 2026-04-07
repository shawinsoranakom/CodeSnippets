def test_makemigrations_field_rename_interactive(self, mock_input):
        class SillyModel(models.Model):
            silly_rename = models.BooleanField(default=False)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(
            module="migrations.test_migrations_no_default",
        ):
            with captured_stdout() as out:
                call_command("makemigrations", "migrations", interactive=True)
        self.assertIn(
            "Rename field silly_field on sillymodel to silly_rename",
            out.getvalue(),
        )