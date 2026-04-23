def test_iterative_dfs_complexity(self):
        """
        In a graph with merge migrations, iterative_dfs() traverses each node
        only once even if there are multiple paths leading to it.
        """
        n = 50
        graph = MigrationGraph()
        for i in range(1, n + 1):
            graph.add_node(("app_a", str(i)), None)
            graph.add_node(("app_b", str(i)), None)
            graph.add_node(("app_c", str(i)), None)
        for i in range(1, n):
            graph.add_dependency(None, ("app_b", str(i)), ("app_a", str(i)))
            graph.add_dependency(None, ("app_c", str(i)), ("app_a", str(i)))
            graph.add_dependency(None, ("app_a", str(i + 1)), ("app_b", str(i)))
            graph.add_dependency(None, ("app_a", str(i + 1)), ("app_c", str(i)))
        plan = graph.forwards_plan(("app_a", str(n)))
        expected = [
            (app, str(i)) for i in range(1, n) for app in ["app_a", "app_c", "app_b"]
        ] + [("app_a", str(n))]
        self.assertEqual(plan, expected)