def test_backwards_nothing_to_do(self):
        r"""
        If the current state satisfies the given target, do nothing.

        a: 1 <--- 2
        b:    \- 1
        c:     \- 1

        If a1 is applied already and a2 is not, and we're asked to migrate to
        a1, don't apply or unapply b1 or c1, regardless of their current state.
        """
        a1_impl = FakeMigration("a1")
        a1 = ("a", "1")
        a2_impl = FakeMigration("a2")
        a2 = ("a", "2")
        b1_impl = FakeMigration("b1")
        b1 = ("b", "1")
        c1_impl = FakeMigration("c1")
        c1 = ("c", "1")
        graph = MigrationGraph()
        graph.add_node(a1, a1_impl)
        graph.add_node(a2, a2_impl)
        graph.add_node(b1, b1_impl)
        graph.add_node(c1, c1_impl)
        graph.add_dependency(None, a2, a1)
        graph.add_dependency(None, b1, a1)
        graph.add_dependency(None, c1, a1)

        executor = MigrationExecutor(None)
        executor.loader = FakeLoader(
            graph,
            {
                a1: a1_impl,
                b1: b1_impl,
            },
        )

        plan = executor.migration_plan({a1})

        self.assertEqual(plan, [])