def test_makemigrations_dry_run(self):
        """
        `makemigrations --dry-run` should not ask for defaults.
        """

        class SillyModel(models.Model):
            silly_field = models.BooleanField(default=False)
            silly_date = models.DateField()  # Added field without a default
            silly_auto_now = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = "migrations"

        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_default"
        ):
            call_command("makemigrations", "migrations", dry_run=True, stdout=out)
        # Output the expected changes directly, without asking for defaults
        self.assertIn("Add field silly_date to sillymodel", out.getvalue())