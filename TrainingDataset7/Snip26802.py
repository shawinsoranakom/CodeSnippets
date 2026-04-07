def test_arrange_for_graph_with_multiple_initial(self):
        # Make a fake graph.
        graph = MigrationGraph()
        # Use project state to make a new migration change set.
        before = self.make_project_state([])
        after = self.make_project_state(
            [self.author_with_book, self.book, self.attribution]
        )
        autodetector = MigrationAutodetector(
            before, after, MigrationQuestioner({"ask_initial": True})
        )
        changes = autodetector._detect_changes()
        changes = autodetector.arrange_for_graph(changes, graph)

        self.assertEqual(changes["otherapp"][0].name, "0001_initial")
        self.assertEqual(changes["otherapp"][0].dependencies, [])
        self.assertEqual(changes["otherapp"][1].name, "0002_initial")
        self.assertCountEqual(
            changes["otherapp"][1].dependencies,
            [("testapp", "0001_initial"), ("otherapp", "0001_initial")],
        )
        self.assertEqual(changes["testapp"][0].name, "0001_initial")
        self.assertEqual(
            changes["testapp"][0].dependencies, [("otherapp", "0001_initial")]
        )