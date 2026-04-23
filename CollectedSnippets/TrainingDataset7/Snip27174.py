def test_fails_squash_migration_manual_porting(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_manual_porting"
        ) as migration_dir:
            version = get_docs_version()
            msg = (
                f"Migration will require manual porting but is already a squashed "
                f"migration.\nTransition to a normal migration first: "
                f"https://docs.djangoproject.com/en/{version}/topics/migrations/"
                f"#squashing-migrations"
            )
            with self.assertRaisesMessage(CommandError, msg):
                call_command("optimizemigration", "migrations", "0004", stdout=out)
            optimized_migration_file = os.path.join(
                migration_dir, "0004_fourth_optimized.py"
            )
            self.assertFalse(os.path.exists(optimized_migration_file))
        self.assertEqual(
            out.getvalue(), "Optimizing from 3 operations to 2 operations.\n"
        )