def test_optimization(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            call_command(
                "optimizemigration", "migrations", "0001", stdout=out, no_color=True
            )
            initial_migration_file = os.path.join(migration_dir, "0001_initial.py")
            self.assertTrue(os.path.exists(initial_migration_file))
            with open(initial_migration_file) as fp:
                content = fp.read()
                self.assertIn(
                    (
                        '("bool", models.BooleanField'
                        if HAS_BLACK
                        else "('bool', models.BooleanField"
                    ),
                    content,
                )
        self.assertEqual(
            out.getvalue(),
            f"Optimizing from 4 operations to 2 operations.\n"
            f"Optimized migration {initial_migration_file}\n",
        )