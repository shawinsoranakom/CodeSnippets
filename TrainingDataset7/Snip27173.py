def test_creates_replace_migration_manual_porting(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_manual_porting"
        ) as migration_dir:
            call_command(
                "optimizemigration", "migrations", "0003", stdout=out, no_color=True
            )
            optimized_migration_file = os.path.join(
                migration_dir, "0003_third_optimized.py"
            )
            self.assertTrue(os.path.exists(optimized_migration_file))
            with open(optimized_migration_file) as fp:
                content = fp.read()
                self.assertIn("replaces = [", content)
        black_warning = ""
        if HAS_BLACK:
            black_warning = (
                "Optimized migration couldn't be formatted using the "
                '"black" command. You can call it manually.\n'
            )
        self.assertEqual(
            out.getvalue(),
            "Optimizing from 3 operations to 2 operations.\n"
            "Manual porting required\n"
            "  Your migrations contained functions that must be manually copied over,\n"
            "  as we could not safely copy their implementation.\n"
            "  See the comment at the top of the optimized migration for details.\n"
            + black_warning
            + f"Optimized migration {optimized_migration_file}\n",
        )