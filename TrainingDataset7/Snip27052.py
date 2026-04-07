def test_sqlmigrate_noop(self):
        out = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001", stdout=out)
        lines = out.getvalue().splitlines()

        if connection.features.can_rollback_ddl:
            lines = lines[1:-1]
        self.assertEqual(
            lines,
            [
                "--",
                "-- Raw SQL operation",
                "--",
                "-- (no-op)",
            ],
        )