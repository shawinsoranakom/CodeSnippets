def test_migrate_check_plan(self):
        out = io.StringIO()
        with self.assertRaises(SystemExit):
            call_command(
                "migrate",
                "migrations",
                "0001",
                check_unapplied=True,
                plan=True,
                stdout=out,
                no_color=True,
            )
        self.assertEqual(
            "Planned operations:\n"
            "migrations.0001_initial\n"
            "    Create model Salamander\n"
            "    Raw Python operation -> Grow salamander tail.\n",
            out.getvalue(),
        )