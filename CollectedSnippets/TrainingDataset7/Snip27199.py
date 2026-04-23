def test_unrelated_model_lookups_forwards(self):
        """
        #24123 - All models of apps already applied which are
        unrelated to the first app being applied are part of the initial model
        state.
        """
        try:
            executor = MigrationExecutor(connection)
            self.assertTableNotExists("lookuperror_a_a1")
            self.assertTableNotExists("lookuperror_b_b1")
            self.assertTableNotExists("lookuperror_c_c1")
            executor.migrate([("lookuperror_b", "0003_b3")])
            self.assertTableExists("lookuperror_b_b3")
            # Rebuild the graph to reflect the new DB state
            executor.loader.build_graph()

            # Migrate forwards -- This led to a lookup LookupErrors because
            # lookuperror_b.B2 is already applied
            executor.migrate(
                [
                    ("lookuperror_a", "0004_a4"),
                    ("lookuperror_c", "0003_c3"),
                ]
            )
            self.assertTableExists("lookuperror_a_a4")
            self.assertTableExists("lookuperror_c_c3")

            # Rebuild the graph to reflect the new DB state
            executor.loader.build_graph()
        finally:
            # Cleanup
            executor.migrate(
                [
                    ("lookuperror_a", None),
                    ("lookuperror_b", None),
                    ("lookuperror_c", None),
                ]
            )
            self.assertTableNotExists("lookuperror_a_a1")
            self.assertTableNotExists("lookuperror_b_b1")
            self.assertTableNotExists("lookuperror_c_c1")