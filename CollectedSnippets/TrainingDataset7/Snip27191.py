def test_migrate_backward_to_squashed_migration(self):
        executor = MigrationExecutor(connection)
        try:
            self.assertTableNotExists("migrations_author")
            self.assertTableNotExists("migrations_book")
            executor.migrate([("migrations", "0001_squashed_0002")])
            self.assertTableExists("migrations_author")
            self.assertTableExists("migrations_book")
            executor.loader.build_graph()
            # Migrate backward to a squashed migration.
            executor.migrate([("migrations", "0001_initial")])
            self.assertTableExists("migrations_author")
            self.assertTableNotExists("migrations_book")
        finally:
            # Unmigrate everything.
            executor = MigrationExecutor(connection)
            executor.migrate([("migrations", None)])
            self.assertTableNotExists("migrations_author")
            self.assertTableNotExists("migrations_book")