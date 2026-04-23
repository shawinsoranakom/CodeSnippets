def test_prune_deleted_squashed_migrations_in_replaces(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed"
        ) as migration_dir:
            try:
                call_command("migrate", "migrations", verbosity=0)
                # Delete the replaced migrations.
                os.remove(os.path.join(migration_dir, "0001_initial.py"))
                os.remove(os.path.join(migration_dir, "0002_second.py"))
                # --prune cannot be used before removing the "replaces"
                # attribute.
                call_command(
                    "migrate",
                    "migrations",
                    prune=True,
                    stdout=out,
                    no_color=True,
                )
                self.assertEqual(
                    out.getvalue(),
                    "Pruning migrations:\n"
                    "  Cannot use --prune because the following squashed "
                    "migrations have their 'replaces' attributes and may not "
                    "be recorded as applied:\n"
                    "    migrations.0001_squashed_0002\n"
                    "  Re-run 'manage.py migrate' if they are not marked as "
                    "applied, and remove 'replaces' attributes in their "
                    "Migration classes.\n",
                )
            finally:
                # Unmigrate everything.
                call_command("migrate", "migrations", "zero", verbosity=0)