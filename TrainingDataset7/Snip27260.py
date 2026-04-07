def test_loading_squashed_complex_multi_apps_partially_applied(self):
        loader = MigrationLoader(connection)
        recorder = MigrationRecorder(connection)
        self.record_applied(recorder, "app1", "1_auto")
        self.record_applied(recorder, "app1", "2_auto")
        loader.build_graph()

        plan = set(loader.graph.forwards_plan(("app1", "4_auto")))
        plan -= loader.applied_migrations.keys()
        expected_plan = {
            ("app2", "1_squashed_2"),
            ("app1", "3_auto"),
            ("app1", "4_auto"),
        }

        self.assertEqual(plan, expected_plan)