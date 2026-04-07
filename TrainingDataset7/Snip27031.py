def test_migrate_check_migrated_app(self):
        out = io.StringIO()
        try:
            call_command("migrate", "migrated_app", verbosity=0)
            call_command(
                "migrate",
                "migrated_app",
                stdout=out,
                check_unapplied=True,
            )
            self.assertEqual(out.getvalue(), "")
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrated_app", "zero", verbosity=0)