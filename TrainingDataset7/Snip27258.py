def test_loading_squashed_complex(self):
        "Tests loading a complex set of squashed migrations"

        loader = MigrationLoader(connection)
        recorder = MigrationRecorder(connection)
        self.addCleanup(recorder.flush)

        def num_nodes():
            plan = set(loader.graph.forwards_plan(("migrations", "7_auto")))
            return len(plan - loader.applied_migrations.keys())

        # Empty database: use squashed migration
        loader.build_graph()
        self.assertEqual(num_nodes(), 5)

        # Starting at 1 or 2 should use the squashed migration too
        self.record_applied(recorder, "migrations", "1_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 4)

        self.record_applied(recorder, "migrations", "2_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 3)

        # However, starting at 3 to 5 cannot use the squashed migration
        self.record_applied(recorder, "migrations", "3_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 4)

        self.record_applied(recorder, "migrations", "4_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 3)

        # Starting at 5 to 7 we are past the squashed migrations.
        self.record_applied(recorder, "migrations", "5_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 2)

        self.record_applied(recorder, "migrations", "6_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 1)

        self.record_applied(recorder, "migrations", "7_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 0)