def test_makemigrations_interactive_unique_callable_default_addition(self):
        """
        makemigrations prompts the user when adding a unique field with
        a callable default.
        """

        class Book(models.Model):
            created = models.DateTimeField(unique=True, default=timezone.now)

            class Meta:
                app_label = "migrations"

        version = get_docs_version()
        input_msg = (
            f"Callable default on unique field book.created will not generate "
            f"unique values upon migrating.\n"
            f"Please choose how to proceed:\n"
            f" 1) Continue making this migration as the first step in writing "
            f"a manual migration to generate unique values described here: "
            f"https://docs.djangoproject.com/en/{version}/howto/"
            f"writing-migrations/#migrations-that-add-unique-fields.\n"
            f" 2) Quit and edit field options in models.py.\n"
        )
        with self.temporary_migration_module(module="migrations.test_migrations"):
            # 2 - quit.
            with mock.patch("builtins.input", return_value="2"):
                with captured_stdout() as out, self.assertRaises(SystemExit):
                    call_command("makemigrations", "migrations", interactive=True)
            out_value = out.getvalue()
            self.assertIn(input_msg, out_value)
            self.assertNotIn("Add field created to book", out_value)
            # 1 - continue.
            with mock.patch("builtins.input", return_value="1"):
                with captured_stdout() as out:
                    call_command("makemigrations", "migrations", interactive=True)
            out_value = out.getvalue()
            self.assertIn(input_msg, out_value)
            self.assertIn("Add field created to book", out_value)