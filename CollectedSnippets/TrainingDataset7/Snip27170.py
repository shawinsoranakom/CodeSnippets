def test_no_optimization_possible(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            call_command(
                "optimizemigration", "migrations", "0002", stdout=out, no_color=True
            )
            migration_file = os.path.join(migration_dir, "0002_second.py")
            self.assertTrue(os.path.exists(migration_file))
            call_command(
                "optimizemigration",
                "migrations",
                "0002",
                stdout=out,
                no_color=True,
                verbosity=0,
            )
        self.assertEqual(out.getvalue(), "No optimizations possible.\n")