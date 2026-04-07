def test_sqlmigrate_forwards(self):
        """
        sqlmigrate outputs forward looking SQL.
        """
        out = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001", stdout=out, no_color=True)

        lines = out.getvalue().splitlines()

        if connection.features.can_rollback_ddl:
            self.assertEqual(lines[0], connection.ops.start_transaction_sql())
            self.assertEqual(lines[-1], connection.ops.end_transaction_sql())
            lines = lines[1:-1]

        self.assertEqual(
            lines[:3],
            [
                "--",
                "-- Create model Author",
                "--",
            ],
        )
        self.assertIn(
            "create table %s" % connection.ops.quote_name("migrations_author").lower(),
            lines[3].lower(),
        )
        pos = lines.index("--", 3)
        self.assertEqual(
            lines[pos : pos + 3],
            [
                "--",
                "-- Create model Tribble",
                "--",
            ],
        )
        self.assertIn(
            "create table %s" % connection.ops.quote_name("migrations_tribble").lower(),
            lines[pos + 3].lower(),
        )
        pos = lines.index("--", pos + 3)
        self.assertEqual(
            lines[pos : pos + 3],
            [
                "--",
                "-- Add field bool to tribble",
                "--",
            ],
        )
        pos = lines.index("--", pos + 3)
        self.assertEqual(
            lines[pos : pos + 3],
            [
                "--",
                "-- Alter unique_together for author (1 constraint(s))",
                "--",
            ],
        )