def test_minimize_rollbacks(self):
        """
        Minimize unnecessary rollbacks in connected apps.

        When you say "./manage.py migrate appA 0001", rather than migrating to
        just after appA-0001 in the linearized migration plan (which could roll
        back migrations in other apps that depend on appA 0001, but don't need
        to be rolled back since we're not rolling back appA 0001), we migrate
        to just before appA-0002.
        """
        a1_impl = FakeMigration("a1")
        a1 = ("a", "1")
        a2_impl = FakeMigration("a2")
        a2 = ("a", "2")
        b1_impl = FakeMigration("b1")
        b1 = ("b", "1")
        graph = MigrationGraph()
        graph.add_node(a1, a1_impl)
        graph.add_node(a2, a2_impl)
        graph.add_node(b1, b1_impl)
        graph.add_dependency(None, b1, a1)
        graph.add_dependency(None, a2, a1)

        executor = MigrationExecutor(None)
        executor.loader = FakeLoader(
            graph,
            {
                a1: a1_impl,
                b1: b1_impl,
                a2: a2_impl,
            },
        )

        plan = executor.migration_plan({a1})

        self.assertEqual(plan, [(a2_impl, True)])