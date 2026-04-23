def test_remove_replacement_node(self):
        """
        A replacement node is properly removed and child dependencies remapped.
        We assume parent dependencies are already correct.
        """
        # Add some dummy nodes to be replaced.
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_a", "0002"), None)
        graph.add_dependency("app_a.0002", ("app_a", "0002"), ("app_a", "0001"))
        # Try removing replacement node before replacement node exists.
        msg = (
            "Unable to remove replacement node ('app_a', '0001_squashed_0002'). It was"
            " either never added to the migration graph, or has been removed already."
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.remove_replacement_node(
                replacement=("app_a", "0001_squashed_0002"),
                replaced=[("app_a", "0001"), ("app_a", "0002")],
            )
        graph.add_node(("app_a", "0001_squashed_0002"), None)
        # Add a child node to test dependency remapping.
        graph.add_node(("app_b", "0001"), None)
        graph.add_dependency(
            "app_b.0001", ("app_b", "0001"), ("app_a", "0001_squashed_0002")
        )
        # Remove the replacement node.
        graph.remove_replacement_node(
            replacement=("app_a", "0001_squashed_0002"),
            replaced=[("app_a", "0001"), ("app_a", "0002")],
        )
        # Ensure graph is consistent and child dependency has been remapped
        graph.validate_consistency()
        replaced_node = graph.node_map[("app_a", "0002")]
        child_node = graph.node_map[("app_b", "0001")]
        self.assertIn(child_node, replaced_node.children)
        self.assertIn(replaced_node, child_node.parents)
        # Child dependency hasn't also gotten remapped to the other replaced
        # node.
        other_replaced_node = graph.node_map[("app_a", "0001")]
        self.assertNotIn(child_node, other_replaced_node.children)
        self.assertNotIn(other_replaced_node, child_node.parents)