def test_marked_as_migrated(self):
        """
        Undefined MIGRATION_MODULES implies default migration module.
        """
        migration_loader = MigrationLoader(connection)
        self.assertEqual(migration_loader.migrated_apps, {"migrated_app"})
        self.assertEqual(migration_loader.unmigrated_apps, set())