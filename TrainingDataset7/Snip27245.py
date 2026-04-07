def test_load(self):
        """
        Makes sure the loader can load the migrations for the test apps,
        and then render them out to a new Apps.
        """
        # Load and test the plan
        migration_loader = MigrationLoader(connection)
        self.assertEqual(
            migration_loader.graph.forwards_plan(("migrations", "0002_second")),
            [
                ("migrations", "0001_initial"),
                ("migrations", "0002_second"),
            ],
        )
        # Now render it out!
        project_state = migration_loader.project_state(("migrations", "0002_second"))
        self.assertEqual(len(project_state.models), 2)

        author_state = project_state.models["migrations", "author"]
        self.assertEqual(
            list(author_state.fields), ["id", "name", "slug", "age", "rating"]
        )

        book_state = project_state.models["migrations", "book"]
        self.assertEqual(list(book_state.fields), ["id", "author"])

        # Ensure we've included unmigrated apps in there too
        self.assertIn("basic", project_state.real_apps)