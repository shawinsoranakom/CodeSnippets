def test_plan_handles_repeated_migrations(self):
        """
        _generate_plan() doesn't readd migrations already in the plan (#29180).
        """
        migration_loader = MigrationLoader(connection)
        nodes = [("migrations", "0002_second"), ("migrations2", "0001_initial")]
        self.assertEqual(
            migration_loader.graph._generate_plan(nodes, at_end=True),
            [
                ("migrations", "0001_initial"),
                ("migrations", "0002_second"),
                ("migrations2", "0001_initial"),
            ],
        )