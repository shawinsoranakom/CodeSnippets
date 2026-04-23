def test_makemigrations_non_interactive_auto_now_add_addition(self):
        """
        Non-interactive makemigrations fails when a default is missing on a
        new field when auto_now_add=True.
        """

        class Entry(models.Model):
            creation_date = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(module="migrations.test_auto_now_add"):
            with self.assertRaises(SystemExit), captured_stdout() as out:
                call_command("makemigrations", "migrations", interactive=False)
        self.assertIn(
            "Field 'creation_date' on model 'entry' not migrated: it is "
            "impossible to add a field with 'auto_now_add=True' without "
            "specifying a default.",
            out.getvalue(),
        )