def test_migrate_plan(self):
        """Tests migrate --plan output."""
        out = io.StringIO()
        # Show the plan up to the third migration.
        call_command(
            "migrate", "migrations", "0003", plan=True, stdout=out, no_color=True
        )
        self.assertEqual(
            "Planned operations:\n"
            "migrations.0001_initial\n"
            "    Create model Salamander\n"
            "    Raw Python operation -> Grow salamander tail.\n"
            "migrations.0002_second\n"
            "    Create model Book\n"
            "    Raw SQL operation -> ['SELECT * FROM migrations_book']\n"
            "migrations.0003_third\n"
            "    Create model Author\n"
            "    Raw SQL operation -> ['SELECT * FROM migrations_author']\n",
            out.getvalue(),
        )
        try:
            # Migrate to the third migration.
            call_command("migrate", "migrations", "0003", verbosity=0)
            out = io.StringIO()
            # Show the plan for when there is nothing to apply.
            call_command(
                "migrate", "migrations", "0003", plan=True, stdout=out, no_color=True
            )
            self.assertEqual(
                "Planned operations:\n  No planned migration operations.\n",
                out.getvalue(),
            )
            out = io.StringIO()
            # Show the plan for reverse migration back to 0001.
            call_command(
                "migrate", "migrations", "0001", plan=True, stdout=out, no_color=True
            )
            self.assertEqual(
                "Planned operations:\n"
                "migrations.0003_third\n"
                "    Undo Create model Author\n"
                "    Raw SQL operation -> ['SELECT * FROM migrations_book']\n"
                "migrations.0002_second\n"
                "    Undo Create model Book\n"
                "    Raw SQL operation -> ['SELECT * FROM migrations_salamand…\n",
                out.getvalue(),
            )
            out = io.StringIO()
            # Show the migration plan to fourth, with truncated details.
            call_command(
                "migrate", "migrations", "0004", plan=True, stdout=out, no_color=True
            )
            self.assertEqual(
                "Planned operations:\n"
                "migrations.0004_fourth\n"
                "    Raw SQL operation -> SELECT * FROM migrations_author WHE…\n",
                out.getvalue(),
            )
            # Show the plan when an operation is irreversible.
            # Migrate to the fourth migration.
            call_command("migrate", "migrations", "0004", verbosity=0)
            out = io.StringIO()
            call_command(
                "migrate", "migrations", "0003", plan=True, stdout=out, no_color=True
            )
            self.assertEqual(
                "Planned operations:\n"
                "migrations.0004_fourth\n"
                "    Raw SQL operation -> IRREVERSIBLE\n",
                out.getvalue(),
            )
            out = io.StringIO()
            call_command(
                "migrate", "migrations", "0005", plan=True, stdout=out, no_color=True
            )
            # Operation is marked as irreversible only in the revert plan.
            self.assertEqual(
                "Planned operations:\n"
                "migrations.0005_fifth\n"
                "    Raw Python operation\n"
                "    Raw Python operation\n"
                "    Raw Python operation -> Feed salamander.\n",
                out.getvalue(),
            )
            call_command("migrate", "migrations", "0005", verbosity=0)
            out = io.StringIO()
            call_command(
                "migrate", "migrations", "0004", plan=True, stdout=out, no_color=True
            )
            self.assertEqual(
                "Planned operations:\n"
                "migrations.0005_fifth\n"
                "    Raw Python operation -> IRREVERSIBLE\n"
                "    Raw Python operation -> IRREVERSIBLE\n"
                "    Raw Python operation\n",
                out.getvalue(),
            )
        finally:
            # Cleanup by unmigrating everything: fake the irreversible, then
            # migrate all to zero.
            call_command("migrate", "migrations", "0003", fake=True, verbosity=0)
            call_command("migrate", "migrations", "zero", verbosity=0)