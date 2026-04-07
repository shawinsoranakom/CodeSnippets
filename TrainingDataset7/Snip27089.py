def test_makemigrations_no_init(self):
        """Migration directories without an __init__.py file are allowed."""
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_init"
        ):
            call_command("makemigrations", stdout=out)
        self.assertIn("0001_initial.py", out.getvalue())