def test_makemigrations_non_interactive_not_null_addition(self):
        """
        Non-interactive makemigrations fails when a default is missing on a
        new not-null field.
        """

        class SillyModel(models.Model):
            silly_field = models.BooleanField(default=False)
            silly_int = models.IntegerField()

            class Meta:
                app_label = "migrations"

        with self.assertRaises(SystemExit):
            with self.temporary_migration_module(
                module="migrations.test_migrations_no_default"
            ):
                with captured_stdout() as out:
                    call_command("makemigrations", "migrations", interactive=False)
        self.assertIn(
            "Field 'silly_int' on model 'sillymodel' not migrated: it is "
            "impossible to add a non-nullable field without specifying a "
            "default.",
            out.getvalue(),
        )