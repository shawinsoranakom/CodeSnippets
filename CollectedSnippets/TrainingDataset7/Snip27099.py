def test_makemigrations_non_interactive_not_null_alteration(self):
        """
        Non-interactive makemigrations fails when a default is missing on a
        field changed to not-null.
        """

        class Author(models.Model):
            name = models.CharField(max_length=255)
            slug = models.SlugField()
            age = models.IntegerField(default=0)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(module="migrations.test_migrations"):
            with captured_stdout() as out:
                call_command("makemigrations", "migrations", interactive=False)
        self.assertIn("Alter field slug on author", out.getvalue())
        self.assertIn(
            "Field 'slug' on model 'author' given a default of NOT PROVIDED "
            "and must be corrected.",
            out.getvalue(),
        )