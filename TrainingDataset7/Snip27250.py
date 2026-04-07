def test_name_match(self):
        "Tests prefix name matching"
        migration_loader = MigrationLoader(connection)
        self.assertEqual(
            migration_loader.get_migration_by_prefix("migrations", "0001").name,
            "0001_initial",
        )
        msg = "There is more than one migration for 'migrations' with the prefix '0'"
        with self.assertRaisesMessage(AmbiguityError, msg):
            migration_loader.get_migration_by_prefix("migrations", "0")
        msg = "There is no migration for 'migrations' with the prefix 'blarg'"
        with self.assertRaisesMessage(KeyError, msg):
            migration_loader.get_migration_by_prefix("migrations", "blarg")