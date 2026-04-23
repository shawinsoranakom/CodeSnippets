def test_soft_apply(self):
        """
        Tests detection of initial migrations already having been applied.
        """
        state = {"faked": None}

        def fake_storer(phase, migration=None, fake=None):
            state["faked"] = fake

        executor = MigrationExecutor(connection, progress_callback=fake_storer)
        # Were the tables there before?
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        # Run it normally
        self.assertEqual(
            executor.migration_plan([("migrations", "0001_initial")]),
            [
                (executor.loader.graph.nodes["migrations", "0001_initial"], False),
            ],
        )
        executor.migrate([("migrations", "0001_initial")])
        # Are the tables there now?
        self.assertTableExists("migrations_author")
        self.assertTableExists("migrations_tribble")
        # We shouldn't have faked that one
        self.assertIs(state["faked"], False)
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()
        # Fake-reverse that
        executor.migrate([("migrations", None)], fake=True)
        # Are the tables still there?
        self.assertTableExists("migrations_author")
        self.assertTableExists("migrations_tribble")
        # Make sure that was faked
        self.assertIs(state["faked"], True)
        # Finally, migrate forwards; this should fake-apply our initial
        # migration
        executor.loader.build_graph()
        self.assertEqual(
            executor.migration_plan([("migrations", "0001_initial")]),
            [
                (executor.loader.graph.nodes["migrations", "0001_initial"], False),
            ],
        )
        # Applying the migration should raise a database level error
        # because we haven't given the --fake-initial option
        with self.assertRaises(DatabaseError):
            executor.migrate([("migrations", "0001_initial")])
        # Reset the faked state
        state = {"faked": None}
        # Allow faking of initial CreateModel operations
        executor.migrate([("migrations", "0001_initial")], fake_initial=True)
        self.assertIs(state["faked"], True)
        # And migrate back to clean up the database
        executor.loader.build_graph()
        executor.migrate([("migrations", None)])
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")