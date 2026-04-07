def test_trim_apps(self):
        """
        Trim does not remove dependencies but does remove unwanted apps.
        """
        # Use project state to make a new migration change set
        before = self.make_project_state([])
        after = self.make_project_state(
            [self.author_empty, self.other_pony, self.other_stable, self.third_thing]
        )
        autodetector = MigrationAutodetector(
            before, after, MigrationQuestioner({"ask_initial": True})
        )
        changes = autodetector._detect_changes()
        # Run through arrange_for_graph
        graph = MigrationGraph()
        changes = autodetector.arrange_for_graph(changes, graph)
        changes["testapp"][0].dependencies.append(("otherapp", "0001_initial"))
        changes = autodetector._trim_to_apps(changes, {"testapp"})
        # Make sure there's the right set of migrations
        self.assertEqual(changes["testapp"][0].name, "0001_initial")
        self.assertEqual(changes["otherapp"][0].name, "0001_initial")
        self.assertNotIn("thirdapp", changes)