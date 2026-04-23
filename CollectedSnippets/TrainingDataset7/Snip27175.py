def test_optimizemigration_check(self):
        with self.assertRaises(SystemExit):
            call_command(
                "optimizemigration", "--check", "migrations", "0001", verbosity=0
            )

        call_command("optimizemigration", "--check", "migrations", "0002", verbosity=0)