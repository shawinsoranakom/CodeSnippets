def test_custom_migration_name(self):
        """Tests custom naming of migrations for graph matching."""
        # Make a fake graph
        graph = MigrationGraph()
        graph.add_node(("testapp", "0001_initial"), None)
        graph.add_node(("testapp", "0002_foobar"), None)
        graph.add_node(("otherapp", "0001_initial"), None)
        graph.add_dependency(
            "testapp.0002_foobar",
            ("testapp", "0002_foobar"),
            ("testapp", "0001_initial"),
        )

        # Use project state to make a new migration change set
        before = self.make_project_state([])
        after = self.make_project_state(
            [self.author_empty, self.other_pony, self.other_stable]
        )
        autodetector = MigrationAutodetector(before, after)
        changes = autodetector._detect_changes()

        # Run through arrange_for_graph
        migration_name = "custom_name"
        changes = autodetector.arrange_for_graph(changes, graph, migration_name)

        # Make sure there's a new name, deps match, etc.
        self.assertEqual(changes["testapp"][0].name, "0003_%s" % migration_name)
        self.assertEqual(
            changes["testapp"][0].dependencies, [("testapp", "0002_foobar")]
        )
        self.assertEqual(changes["otherapp"][0].name, "0002_%s" % migration_name)
        self.assertEqual(
            changes["otherapp"][0].dependencies, [("otherapp", "0001_initial")]
        )