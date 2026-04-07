def test_load_unmigrated_dependency(self):
        """
        The loader can load migrations with a dependency on an unmigrated app.
        """
        # Load and test the plan
        migration_loader = MigrationLoader(connection)
        self.assertEqual(
            migration_loader.graph.forwards_plan(("migrations", "0001_initial")),
            [
                ("contenttypes", "0001_initial"),
                ("auth", "0001_initial"),
                ("migrations", "0001_initial"),
            ],
        )
        # Now render it out!
        project_state = migration_loader.project_state(("migrations", "0001_initial"))
        self.assertEqual(
            len([m for a, m in project_state.models if a == "migrations"]), 1
        )

        book_state = project_state.models["migrations", "book"]
        self.assertEqual(list(book_state.fields), ["id", "user"])