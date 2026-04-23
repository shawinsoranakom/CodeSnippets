def test_makemigrations_non_interactive_no_field_rename(self):
        """
        makemigrations adds and removes a possible field rename in
        non-interactive mode.
        """

        class SillyModel(models.Model):
            silly_rename = models.BooleanField(default=False)

            class Meta:
                app_label = "migrations"

        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_default"
        ):
            call_command("makemigrations", "migrations", interactive=False, stdout=out)
        self.assertIn("Remove field silly_field from sillymodel", out.getvalue())
        self.assertIn("Add field silly_rename to sillymodel", out.getvalue())