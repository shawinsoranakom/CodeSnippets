def test_iterative_dfs(self):
        graph = MigrationGraph()
        root = ("app_a", "1")
        graph.add_node(root, None)
        expected = [root]
        for i in range(2, 750):
            parent = ("app_a", str(i - 1))
            child = ("app_a", str(i))
            graph.add_node(child, None)
            graph.add_dependency(str(i), child, parent)
            expected.append(child)
        leaf = expected[-1]

        forwards_plan = graph.forwards_plan(leaf)
        self.assertEqual(expected, forwards_plan)

        backwards_plan = graph.backwards_plan(root)
        self.assertEqual(expected[::-1], backwards_plan)