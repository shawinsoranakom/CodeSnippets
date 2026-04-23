def test_empty_plan(self):
        """
        Re-planning a full migration of a fully-migrated set doesn't
        perform spurious unmigrations and remigrations.

        There was previously a bug where the executor just always performed the
        backwards plan for applied migrations - which even for the most recent
        migration in an app, might include other, dependent apps, and these
        were being unmigrated.
        """
        # Make the initial plan, check it
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(
            [
                ("migrations", "0002_second"),
                ("migrations2", "0001_initial"),
            ]
        )
        self.assertEqual(
            plan,
            [
                (executor.loader.graph.nodes["migrations", "0001_initial"], False),
                (executor.loader.graph.nodes["migrations", "0002_second"], False),
                (executor.loader.graph.nodes["migrations2", "0001_initial"], False),
            ],
        )
        # Fake-apply all migrations
        executor.migrate(
            [("migrations", "0002_second"), ("migrations2", "0001_initial")], fake=True
        )
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()
        # Now plan a second time and make sure it's empty
        plan = executor.migration_plan(
            [
                ("migrations", "0002_second"),
                ("migrations2", "0001_initial"),
            ]
        )
        self.assertEqual(plan, [])
        # The resulting state should include applied migrations.
        state = executor.migrate(
            [
                ("migrations", "0002_second"),
                ("migrations2", "0001_initial"),
            ]
        )
        self.assertIn(("migrations", "book"), state.models)
        self.assertIn(("migrations", "author"), state.models)
        self.assertIn(("migrations2", "otherauthor"), state.models)
        # Erase all the fake records
        executor.recorder.record_unapplied("migrations2", "0001_initial")
        executor.recorder.record_unapplied("migrations", "0002_second")
        executor.recorder.record_unapplied("migrations", "0001_initial")