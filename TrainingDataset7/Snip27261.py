def test_loading_squashed_erroneous(self):
        "Tests loading a complex but erroneous set of squashed migrations"

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

        # However, starting at 3 or 4, nonexistent migrations would be needed.
        msg = (
            "Migration migrations.6_auto depends on nonexistent node "
            "('migrations', '5_auto'). Django tried to replace migration "
            "migrations.5_auto with any of [migrations.3_squashed_5] but wasn't able "
            "to because some of the replaced migrations are already applied."
        )

        self.record_applied(recorder, "migrations", "3_auto")
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            loader.build_graph()

        self.record_applied(recorder, "migrations", "4_auto")
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            loader.build_graph()

        # Starting at 5 to 7 we are passed the squashed migrations
        self.record_applied(recorder, "migrations", "5_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 2)

        self.record_applied(recorder, "migrations", "6_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 1)

        self.record_applied(recorder, "migrations", "7_auto")
        loader.build_graph()
        self.assertEqual(num_nodes(), 0)