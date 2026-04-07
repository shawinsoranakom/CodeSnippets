def test_squashmigrations_valid_start(self):
        """
        squashmigrations accepts a starting migration.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_changes"
        ) as migration_dir:
            call_command(
                "squashmigrations",
                "migrations",
                "0002",
                "0003",
                interactive=False,
                verbosity=1,
                stdout=out,
            )

            squashed_migration_file = os.path.join(
                migration_dir, "0002_second_squashed_0003_third.py"
            )
            with open(squashed_migration_file, encoding="utf-8") as fp:
                content = fp.read()
                if HAS_BLACK:
                    test_str = '        ("migrations", "0001_initial")'
                else:
                    test_str = "        ('migrations', '0001_initial')"
                self.assertIn(test_str, content)
                self.assertNotIn("initial = True", content)
        out = out.getvalue()
        self.assertNotIn(" - 0001_initial", out)
        self.assertIn(" - 0002_second", out)
        self.assertIn(" - 0003_third", out)