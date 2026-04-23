def test_sqlmigrate_backwards(self):
        """
        sqlmigrate outputs reverse looking SQL.
        """
        # Cannot generate the reverse SQL unless we've applied the migration.
        call_command("migrate", "migrations", verbosity=0)

        out = io.StringIO()
        call_command(
            "sqlmigrate",
            "migrations",
            "0001",
            stdout=out,
            backwards=True,
            no_color=True,
        )

        lines = out.getvalue().splitlines()
        try:
            if connection.features.can_rollback_ddl:
                self.assertEqual(lines[0], connection.ops.start_transaction_sql())
                self.assertEqual(lines[-1], connection.ops.end_transaction_sql())
                lines = lines[1:-1]

            self.assertEqual(
                lines[:3],
                [
                    "--",
                    "-- Alter unique_together for author (1 constraint(s))",
                    "--",
                ],
            )
            pos = lines.index("--", 3)
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
                    "-- Create model Tribble",
                    "--",
                ],
            )
            next_pos = lines.index("--", pos + 3)
            drop_table_sql = (
                "drop table %s"
                % connection.ops.quote_name("migrations_tribble").lower()
            )
            for line in lines[pos + 3 : next_pos]:
                if drop_table_sql in line.lower():
                    break
            else:
                self.fail("DROP TABLE (tribble) not found.")
            pos = next_pos
            self.assertEqual(
                lines[pos : pos + 3],
                [
                    "--",
                    "-- Create model Author",
                    "--",
                ],
            )
            drop_table_sql = (
                "drop table %s" % connection.ops.quote_name("migrations_author").lower()
            )
            for line in lines[pos + 3 :]:
                if drop_table_sql in line.lower():
                    break
            else:
                self.fail("DROP TABLE (author) not found.")
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)