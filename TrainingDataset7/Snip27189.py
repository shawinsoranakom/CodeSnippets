def test_run(self):
        """
        Tests running a simple set of migrations.
        """
        executor = MigrationExecutor(connection)
        # Let's look at the plan first and make sure it's up to scratch
        plan = executor.migration_plan([("migrations", "0002_second")])
        self.assertEqual(
            plan,
            [
                (executor.loader.graph.nodes["migrations", "0001_initial"], False),
                (executor.loader.graph.nodes["migrations", "0002_second"], False),
            ],
        )
        # Were the tables there before?
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_book")
        # Alright, let's try running it
        executor.migrate([("migrations", "0002_second")])
        # Are the tables there now?
        self.assertTableExists("migrations_author")
        self.assertTableExists("migrations_book")
        # Rebuild the graph to reflect the new DB state
        executor.loader.build_graph()
        # Alright, let's undo what we did
        plan = executor.migration_plan([("migrations", None)])
        self.assertEqual(
            plan,
            [
                (executor.loader.graph.nodes["migrations", "0002_second"], True),
                (executor.loader.graph.nodes["migrations", "0001_initial"], True),
            ],
        )
        executor.migrate([("migrations", None)])
        # Are the tables gone?
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_book")