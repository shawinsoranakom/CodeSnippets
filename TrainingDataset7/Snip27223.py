def test_circular_graph_2(self):
        graph = MigrationGraph()
        graph.add_node(("A", "0001"), None)
        graph.add_node(("C", "0001"), None)
        graph.add_node(("B", "0001"), None)
        graph.add_dependency("A.0001", ("A", "0001"), ("B", "0001"))
        graph.add_dependency("B.0001", ("B", "0001"), ("A", "0001"))
        graph.add_dependency("C.0001", ("C", "0001"), ("B", "0001"))

        with self.assertRaises(CircularDependencyError):
            graph.ensure_not_cyclic()