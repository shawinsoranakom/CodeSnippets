def test_stringify(self):
        graph = MigrationGraph()
        self.assertEqual(str(graph), "Graph: 0 nodes, 0 edges")

        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_a", "0002"), None)
        graph.add_node(("app_a", "0003"), None)
        graph.add_node(("app_b", "0001"), None)
        graph.add_node(("app_b", "0002"), None)
        graph.add_dependency("app_a.0002", ("app_a", "0002"), ("app_a", "0001"))
        graph.add_dependency("app_a.0003", ("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency("app_a.0003", ("app_a", "0003"), ("app_b", "0002"))

        self.assertEqual(str(graph), "Graph: 5 nodes, 3 edges")
        self.assertEqual(repr(graph), "<MigrationGraph: nodes=5, edges=3>")