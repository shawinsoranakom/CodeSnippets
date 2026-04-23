def test_migrate_marks_replacement_unapplied(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("migrations", "0001_squashed_0002")])
        try:
            self.assertIn(
                ("migrations", "0001_squashed_0002"),
                executor.recorder.applied_migrations(),
            )
        finally:
            executor.loader.build_graph()
            executor.migrate([("migrations", None)])
            self.assertNotIn(
                ("migrations", "0001_squashed_0002"),
                executor.recorder.applied_migrations(),
            )