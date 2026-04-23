def test_loading_squashed_ref_squashed(self):
        """
        Tests loading a squashed migration with a new migration referencing it
        """
        r"""
        The sample migrations are structured like this:

        app_1       1 --> 2 ---------------------*--> 3        *--> 4
                     \                          /             /
                      *-------------------*----/--> 2_sq_3 --*
                       \                 /    /
        =============== \ ============= / == / ======================
        app_2            *--> 1_sq_2 --*    /
                          \                /
                           *--> 1 --> 2 --*

        Where 2_sq_3 is a replacing migration for 2 and 3 in app_1,
        as 1_sq_2 is a replacing migration for 1 and 2 in app_2.
        """

        loader = MigrationLoader(connection)
        recorder = MigrationRecorder(connection)
        self.addCleanup(recorder.flush)

        # Load with nothing applied: both migrations squashed.
        loader.build_graph()
        plan = set(loader.graph.forwards_plan(("app1", "4_auto")))
        plan -= loader.applied_migrations.keys()
        expected_plan = {
            ("app1", "1_auto"),
            ("app2", "1_squashed_2"),
            ("app1", "2_squashed_3"),
            ("app1", "4_auto"),
        }
        self.assertEqual(plan, expected_plan)

        # Load with nothing applied and migrate to a replaced migration.
        # Not possible if loader.replace_migrations is True (default).
        loader.build_graph()
        msg = "Node ('app1', '3_auto') not a valid node"
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            loader.graph.forwards_plan(("app1", "3_auto"))
        # Possible if loader.replace_migrations is False.
        loader.replace_migrations = False
        loader.build_graph()
        plan = set(loader.graph.forwards_plan(("app1", "3_auto")))
        plan -= loader.applied_migrations.keys()
        expected_plan = {
            ("app1", "1_auto"),
            ("app2", "1_auto"),
            ("app2", "2_auto"),
            ("app1", "2_auto"),
            ("app1", "3_auto"),
        }
        self.assertEqual(plan, expected_plan)
        loader.replace_migrations = True

        # Fake-apply a few from app1: unsquashes migration in app1.
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

        # Fake-apply one from app2: unsquashes migration in app2 too.
        self.record_applied(recorder, "app2", "1_auto")
        loader.build_graph()
        plan = set(loader.graph.forwards_plan(("app1", "4_auto")))
        plan -= loader.applied_migrations.keys()
        expected_plan = {
            ("app2", "2_auto"),
            ("app1", "3_auto"),
            ("app1", "4_auto"),
        }
        self.assertEqual(plan, expected_plan)