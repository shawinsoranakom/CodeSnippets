def test_mixed_plan_not_supported(self):
        """
        Although the MigrationExecutor interfaces allows for mixed migration
        plans (combined forwards and backwards migrations) this is not
        supported.
        """
        # Prepare for mixed plan
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan([("migrations", "0002_second")])
        self.assertEqual(
            plan,
            [
                (executor.loader.graph.nodes["migrations", "0001_initial"], False),
                (executor.loader.graph.nodes["migrations", "0002_second"], False),
            ],
        )
        executor.migrate(None, plan)
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()
        self.assertIn(
            ("migrations", "0001_initial"), executor.loader.applied_migrations
        )
        self.assertIn(("migrations", "0002_second"), executor.loader.applied_migrations)
        self.assertNotIn(
            ("migrations2", "0001_initial"), executor.loader.applied_migrations
        )

        # Generate mixed plan
        plan = executor.migration_plan(
            [
                ("migrations", None),
                ("migrations2", "0001_initial"),
            ]
        )
        msg = (
            "Migration plans with both forwards and backwards migrations are "
            "not supported. Please split your migration process into separate "
            "plans of only forwards OR backwards migrations."
        )
        with self.assertRaisesMessage(InvalidMigrationPlan, msg) as cm:
            executor.migrate(None, plan)
        self.assertEqual(
            cm.exception.args[1],
            [
                (executor.loader.graph.nodes["migrations", "0002_second"], True),
                (executor.loader.graph.nodes["migrations", "0001_initial"], True),
                (executor.loader.graph.nodes["migrations2", "0001_initial"], False),
            ],
        )
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()
        executor.migrate(
            [
                ("migrations", None),
                ("migrations2", None),
            ]
        )
        # Are the tables gone?
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_book")
        self.assertTableNotExists("migrations2_otherauthor")