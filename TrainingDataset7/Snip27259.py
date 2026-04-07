def test_loading_squashed_complex_multi_apps(self):
        loader = MigrationLoader(connection)
        loader.build_graph()

        plan = set(loader.graph.forwards_plan(("app1", "4_auto")))
        expected_plan = {
            ("app1", "1_auto"),
            ("app2", "1_squashed_2"),
            ("app1", "2_squashed_3"),
            ("app1", "4_auto"),
        }
        self.assertEqual(plan, expected_plan)