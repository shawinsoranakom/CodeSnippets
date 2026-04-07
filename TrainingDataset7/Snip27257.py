def test_loading_squashed(self):
        "Tests loading a squashed migration"
        migration_loader = MigrationLoader(connection)
        recorder = MigrationRecorder(connection)
        self.addCleanup(recorder.flush)
        # Loading with nothing applied should just give us the one node
        self.assertEqual(
            len([x for x in migration_loader.graph.nodes if x[0] == "migrations"]),
            1,
        )
        # However, fake-apply one migration and it should now use the old two
        self.record_applied(recorder, "migrations", "0001_initial")
        migration_loader.build_graph()
        self.assertEqual(
            len([x for x in migration_loader.graph.nodes if x[0] == "migrations"]),
            2,
        )