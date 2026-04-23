def test_missing_child_nodes(self):
        """
        Tests for missing child nodes.
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        msg = (
            "Migration app_a.0002 dependencies reference nonexistent child node "
            "('app_a', '0002')"
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.add_dependency("app_a.0002", ("app_a", "0002"), ("app_a", "0001"))