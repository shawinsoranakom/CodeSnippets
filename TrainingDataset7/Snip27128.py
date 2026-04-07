def test_makemigrations_auto_now_add_interactive(self, *args):
        """
        makemigrations prompts the user when adding auto_now_add to an existing
        model.
        """

        class Entry(models.Model):
            title = models.CharField(max_length=255)
            creation_date = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = "migrations"

        input_msg = (
            "It is impossible to add the field 'creation_date' with "
            "'auto_now_add=True' to entry without providing a default. This "
            "is because the database needs something to populate existing "
            "rows.\n"
            " 1) Provide a one-off default now which will be set on all "
            "existing rows\n"
            " 2) Quit and manually define a default value in models.py."
        )
        # Monkeypatch interactive questioner to auto accept
        prompt_stdout = io.StringIO()
        with self.temporary_migration_module(module="migrations.test_auto_now_add"):
            call_command(
                "makemigrations", "migrations", interactive=True, stdout=prompt_stdout
            )
        prompt_output = prompt_stdout.getvalue()
        self.assertIn(input_msg, prompt_output)
        self.assertIn("Please enter the default value as valid Python.", prompt_output)
        self.assertIn(
            "Accept the default 'timezone.now' by pressing 'Enter' or provide "
            "another value.",
            prompt_output,
        )
        self.assertIn("Type 'exit' to exit this prompt", prompt_output)
        self.assertIn("Add field creation_date to entry", prompt_output)