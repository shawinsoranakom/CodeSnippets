def test_makemigrations_interactive_not_null_addition(self):
        """
        makemigrations messages when adding a NOT NULL field in interactive
        mode.
        """

        class Author(models.Model):
            silly_field = models.BooleanField(null=False)

            class Meta:
                app_label = "migrations"

        input_msg = (
            "It is impossible to add a non-nullable field 'silly_field' to "
            "author without specifying a default. This is because the "
            "database needs something to populate existing rows.\n"
            "Please select a fix:\n"
            " 1) Provide a one-off default now (will be set on all existing "
            "rows with a null value for this column)\n"
            " 2) Quit and manually define a default value in models.py."
        )
        with self.temporary_migration_module(module="migrations.test_migrations"):
            # 2 - quit.
            with mock.patch("builtins.input", return_value="2"):
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