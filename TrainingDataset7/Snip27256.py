def test_explicit_missing_module(self):
        """
        If a MIGRATION_MODULES override points to a missing module, the error
        raised during the importation attempt should be propagated unless
        `ignore_no_migrations=True`.
        """
        with self.assertRaisesMessage(ImportError, "missing-module"):
            migration_loader = MigrationLoader(connection)
        migration_loader = MigrationLoader(connection, ignore_no_migrations=True)
        self.assertEqual(migration_loader.migrated_apps, set())
        self.assertEqual(migration_loader.unmigrated_apps, {"migrated_app"})