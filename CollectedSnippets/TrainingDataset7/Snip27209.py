def test_migrate_skips_schema_creation(self, mocked_has_table):
        """
        The django_migrations table is not created if there are no migrations
        to record.
        """
        executor = MigrationExecutor(connection)
        # 0 queries, since the query for has_table is being mocked.
        with self.assertNumQueries(0):
            executor.migrate([], plan=[])