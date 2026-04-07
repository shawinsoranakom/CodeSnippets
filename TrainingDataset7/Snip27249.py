def test_first(self):
        """
        Makes sure the '__first__' migrations build correctly.
        """
        migration_loader = MigrationLoader(connection)
        self.assertEqual(
            migration_loader.graph.forwards_plan(("migrations", "second")),
            [
                ("migrations", "thefirst"),
                ("migrations2", "0001_initial"),
                ("migrations2", "0002_second"),
                ("migrations", "second"),
            ],
        )