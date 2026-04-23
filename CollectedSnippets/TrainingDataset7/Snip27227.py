def test_missing_parent_nodes(self):
        """
        Tests for missing parent nodes.
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_a", "0002"), None)
        graph.add_node(("app_a", "0003"), None)
        graph.add_node(("app_b", "0001"), None)
        graph.add_dependency("app_a.0003", ("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency("app_a.0002", ("app_a", "0002"), ("app_a", "0001"))
        msg = (
            "Migration app_a.0001 dependencies reference nonexistent parent node "
            "('app_b', '0002')"
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.add_dependency("app_a.0001", ("app_a", "0001"), ("app_b", "0002"))