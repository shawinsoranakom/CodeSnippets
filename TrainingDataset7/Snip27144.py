def test_squashmigrations_squashes_already_squashed(self):
        out = io.StringIO()

        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed_complex"
        ):
            call_command(
                "squashmigrations",
                "migrations",
                "3_squashed_5",
                "--squashed-name",
                "double_squash",
                stdout=out,
                interactive=False,
            )

            loader = MigrationLoader(connection)
            migration = loader.disk_migrations[("migrations", "0001_double_squash")]
            # Confirm the replaces mechanism holds the squashed migration
            # (and not what it squashes, as the squash operations are what
            # end up being used).
            self.assertEqual(
                migration.replaces,
                [
                    ("migrations", "1_auto"),
                    ("migrations", "2_auto"),
                    ("migrations", "3_squashed_5"),
                ],
            )

            out = io.StringIO()
            call_command(
                "migrate", "migrations", "--plan", interactive=False, stdout=out
            )

            migration_plan = re.findall("migrations.(.+)\n", out.getvalue())
            self.assertEqual(migration_plan, ["0001_double_squash", "6_auto", "7_auto"])