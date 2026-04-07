def test_prune_no_migrations_to_prune(self):
        out = io.StringIO()
        call_command("migrate", "migrations", prune=True, stdout=out, no_color=True)
        self.assertEqual(
            out.getvalue(),
            "Pruning migrations:\n  No migrations to prune.\n",
        )
        out = io.StringIO()
        call_command(
            "migrate",
            "migrations",
            prune=True,
            stdout=out,
            no_color=True,
            verbosity=0,
        )
        self.assertEqual(out.getvalue(), "")