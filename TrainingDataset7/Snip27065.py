def test_migrate_backward_to_squashed_migration(self):
        try:
            call_command("migrate", "migrations", "0001_squashed_0002", verbosity=0)
            self.assertTableExists("migrations_author")
            self.assertTableExists("migrations_book")
            call_command("migrate", "migrations", "0001_initial", verbosity=0)
            self.assertTableExists("migrations_author")
            self.assertTableNotExists("migrations_book")
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)