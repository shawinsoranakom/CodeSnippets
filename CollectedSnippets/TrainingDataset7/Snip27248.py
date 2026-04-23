def test_run_before(self):
        """
        Makes sure the loader uses Migration.run_before.
        """
        # Load and test the plan
        migration_loader = MigrationLoader(connection)
        self.assertEqual(
            migration_loader.graph.forwards_plan(("migrations", "0002_second")),
            [
                ("migrations", "0001_initial"),
                ("migrations", "0003_third"),
                ("migrations", "0002_second"),
            ],
        )