def test_migrate_check(self):
        with self.assertRaises(SystemExit):
            call_command("migrate", "migrations", "0001", check_unapplied=True)
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        self.assertTableNotExists("migrations_book")