def test_squash_partially_applied(self):
        """
        Replacement migrations are partially applied. Then we squash again and
        verify that only unapplied migrations will be applied by "migrate".
        """
        out = io.StringIO()

        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed_partially_applied"
        ):
            # Apply first 2 migrations.
            call_command("migrate", "migrations", "0002", interactive=False, stdout=out)

            # Squash the 2 migrations, that we just applied + 1 more.
            call_command(
                "squashmigrations",
                "migrations",
                "0001",
                "0003",
                "--squashed-name",
                "squashed_0001_0003",
                stdout=out,
                interactive=False,
            )

            # Update the 4th migration to depend on the squash(replacement)
            # migration.
            loader = MigrationLoader(connection)
            migration = loader.disk_migrations[
                ("migrations", "0004_remove_mymodel1_field_1_mymodel1_field_3_and_more")
            ]
            migration.dependencies = [("migrations", "0001_squashed_0001_0003")]
            writer = MigrationWriter(migration)
            with open(writer.path, "w", encoding="utf-8") as fh:
                fh.write(writer.as_string())

            # Squash the squash(replacement) migration with the 4th migration.
            call_command(
                "squashmigrations",
                "migrations",
                "0001_squashed_0001_0003",
                "0004",
                "--squashed-name",
                "squashed_0001_0004",
                stdout=out,
                interactive=False,
            )

            loader = MigrationLoader(connection)
            migration = loader.disk_migrations[
                ("migrations", "0001_squashed_0001_0004")
            ]
            self.assertEqual(
                migration.replaces,
                [
                    ("migrations", "0001_squashed_0001_0003"),
                    (
                        "migrations",
                        "0004_remove_mymodel1_field_1_mymodel1_field_3_and_more",
                    ),
                ],
            )

            # Verify that only unapplied migrations will be applied.
            out = io.StringIO()
            call_command(
                "migrate", "migrations", "--plan", interactive=False, stdout=out
            )

            migration_plan = re.findall("migrations.(.+)\n", out.getvalue())
            self.assertEqual(
                migration_plan,
                [
                    "0003_alter_mymodel2_unique_together",
                    "0004_remove_mymodel1_field_1_mymodel1_field_3_and_more",
                ],
            )