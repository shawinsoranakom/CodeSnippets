def test_migrate_forward_to_squashed_migration(self):
        try:
            call_command("migrate", "migrations", "0001_initial", verbosity=0)
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)