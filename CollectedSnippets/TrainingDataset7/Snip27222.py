def test_circular_graph(self):
        """
        Tests a circular dependency graph.
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_a", "0002"), None)
        graph.add_node(("app_a", "0003"), None)
        graph.add_node(("app_b", "0001"), None)
        graph.add_node(("app_b", "0002"), None)
        graph.add_dependency("app_a.0003", ("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency("app_a.0002", ("app_a", "0002"), ("app_a", "0001"))
        graph.add_dependency("app_a.0001", ("app_a", "0001"), ("app_b", "0002"))
        graph.add_dependency("app_b.0002", ("app_b", "0002"), ("app_b", "0001"))
        graph.add_dependency("app_b.0001", ("app_b", "0001"), ("app_a", "0003"))
        # Test whole graph
        with self.assertRaises(CircularDependencyError):
            graph.ensure_not_cyclic()