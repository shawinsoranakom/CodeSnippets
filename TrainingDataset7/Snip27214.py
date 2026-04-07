def test_minimize_rollbacks_branchy(self):
        r"""
        Minimize rollbacks when target has multiple in-app children.

        a: 1 <---- 3 <--\
              \ \- 2 <--- 4
               \       \
        b:      \- 1 <--- 2
        """
        a1_impl = FakeMigration("a1")
        a1 = ("a", "1")
        a2_impl = FakeMigration("a2")
        a2 = ("a", "2")
        a3_impl = FakeMigration("a3")
        a3 = ("a", "3")
        a4_impl = FakeMigration("a4")
        a4 = ("a", "4")
        b1_impl = FakeMigration("b1")
        b1 = ("b", "1")
        b2_impl = FakeMigration("b2")
        b2 = ("b", "2")
        graph = MigrationGraph()
        graph.add_node(a1, a1_impl)
        graph.add_node(a2, a2_impl)
        graph.add_node(a3, a3_impl)
        graph.add_node(a4, a4_impl)
        graph.add_node(b1, b1_impl)
        graph.add_node(b2, b2_impl)
        graph.add_dependency(None, a2, a1)
        graph.add_dependency(None, a3, a1)
        graph.add_dependency(None, a4, a2)
        graph.add_dependency(None, a4, a3)
        graph.add_dependency(None, b2, b1)
        graph.add_dependency(None, b1, a1)
        graph.add_dependency(None, b2, a2)

        executor = MigrationExecutor(None)
        executor.loader = FakeLoader(
            graph,
            {
                a1: a1_impl,
                b1: b1_impl,
                a2: a2_impl,
                b2: b2_impl,
                a3: a3_impl,
                a4: a4_impl,
            },
        )

        plan = executor.migration_plan({a1})

        should_be_rolled_back = [b2_impl, a4_impl, a2_impl, a3_impl]
        exp = [(m, True) for m in should_be_rolled_back]
        self.assertEqual(plan, exp)