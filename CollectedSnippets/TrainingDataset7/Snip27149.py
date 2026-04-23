def test_squashmigrations_optimizes(self):
        """
        squashmigrations optimizes operations.
        """
        out = io.StringIO()
        with self.temporary_migration_module(module="migrations.test_migrations"):
            call_command(
                "squashmigrations",
                "migrations",
                "0002",
                interactive=False,
                verbosity=1,
                stdout=out,
            )
        self.assertIn("Optimized from 8 operations to 2 operations.", out.getvalue())