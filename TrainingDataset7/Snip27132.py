def test_makemigrations_non_interactive_unique_callable_default_addition(self):
        class Book(models.Model):
            created = models.DateTimeField(unique=True, default=timezone.now)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(module="migrations.test_migrations"):
            with captured_stdout() as out:
                call_command("makemigrations", "migrations", interactive=False)
            out_value = out.getvalue()
            self.assertIn("Add field created to book", out_value)