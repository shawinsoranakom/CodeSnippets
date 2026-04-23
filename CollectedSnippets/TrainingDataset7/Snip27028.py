def test_migrate_fake_split_initial(self):
        """
        Split initial migrations can be faked with --fake-initial.
        """
        try:
            call_command("migrate", "migrations", "0002", verbosity=0)
            call_command("migrate", "migrations", "zero", fake=True, verbosity=0)
            out = io.StringIO()
            with mock.patch(
                "django.core.management.color.supports_color", lambda *args: False
            ):
                call_command(
                    "migrate",
                    "migrations",
                    "0002",
                    fake_initial=True,
                    stdout=out,
                    verbosity=1,
                )
            value = out.getvalue().lower()
            self.assertIn("migrations.0001_initial... faked", value)
            self.assertIn("migrations.0002_second... faked", value)
        finally:
            # Fake an apply.
            call_command("migrate", "migrations", fake=True, verbosity=0)
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)