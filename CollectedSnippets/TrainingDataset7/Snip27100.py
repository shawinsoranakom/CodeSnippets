def test_makemigrations_interactive_not_null_alteration(self):
        """
        makemigrations messages when changing a NULL field to NOT NULL in
        interactive mode.
        """

        class Author(models.Model):
            slug = models.SlugField(null=False)

            class Meta:
                app_label = "migrations"

        input_msg = (
            "It is impossible to change a nullable field 'slug' on author to "
            "non-nullable without providing a default. This is because the "
            "database needs something to populate existing rows.\n"
            "Please select a fix:\n"
            " 1) Provide a one-off default now (will be set on all existing "
            "rows with a null value for this column)\n"
            " 2) Ignore for now. Existing rows that contain NULL values will "
            "have to be handled manually, for example with a RunPython or "
            "RunSQL operation.\n"
            " 3) Quit and manually define a default value in models.py."
        )
        with self.temporary_migration_module(module="migrations.test_migrations"):
            # No message appears if --dry-run.
            with captured_stdout() as out:
                call_command(
                    "makemigrations",
                    "migrations",
                    interactive=True,
                    dry_run=True,
                )
            self.assertNotIn(input_msg, out.getvalue())
            # 3 - quit.
            with mock.patch("builtins.input", return_value="3"):
                with captured_stdout() as out, self.assertRaises(SystemExit):
                    call_command("makemigrations", "migrations", interactive=True)
            self.assertIn(input_msg, out.getvalue())
            # 1 - provide a default.
            with mock.patch("builtins.input", return_value="1"):
                with captured_stdout() as out:
                    call_command("makemigrations", "migrations", interactive=True)
            output = out.getvalue()
            self.assertIn(input_msg, output)
            self.assertIn("Please enter the default value as valid Python.", output)
            self.assertIn(
                "The datetime and django.utils.timezone modules are "
                "available, so it is possible to provide e.g. timezone.now as "
                "a value",
                output,
            )
            self.assertIn("Type 'exit' to exit this prompt", output)