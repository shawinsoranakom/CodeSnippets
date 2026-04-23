def test_ticket_23799_squashmigrations_no_optimize(self):
        """
        squashmigrations --no-optimize doesn't optimize operations.
        """
        out = io.StringIO()
        with self.temporary_migration_module(module="migrations.test_migrations"):
            call_command(
                "squashmigrations",
                "migrations",
                "0002",
                interactive=False,
                verbosity=1,
                no_optimize=True,
                stdout=out,
            )
        self.assertIn("Skipping optimization", out.getvalue())