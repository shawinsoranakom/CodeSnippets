def test_remove_replaced_nodes(self):
        """
        Replaced nodes are properly removed and dependencies remapped.
        """
        # Add some dummy nodes to be replaced.
        graph = MigrationGraph()
        graph.add_dummy_node(
            key=("app_a", "0001"), origin="app_a.0002", error_message="BAD!"
        )
        graph.add_dummy_node(
            key=("app_a", "0002"), origin="app_b.0001", error_message="BAD!"
        )
        graph.add_dependency(
            "app_a.0002", ("app_a", "0002"), ("app_a", "0001"), skip_validation=True
        )
        # Add some normal parent and child nodes to test dependency remapping.
        graph.add_node(("app_c", "0001"), None)
        graph.add_node(("app_b", "0001"), None)
        graph.add_dependency(
            "app_a.0001", ("app_a", "0001"), ("app_c", "0001"), skip_validation=True
        )
        graph.add_dependency(
            "app_b.0001", ("app_b", "0001"), ("app_a", "0002"), skip_validation=True
        )
        # Try replacing before replacement node exists.
        msg = (
            "Unable to find replacement node ('app_a', '0001_squashed_0002'). It was "
            "either never added to the migration graph, or has been removed."
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.remove_replaced_nodes(
                replacement=("app_a", "0001_squashed_0002"),
                replaced=[("app_a", "0001"), ("app_a", "0002")],
            )
        graph.add_node(("app_a", "0001_squashed_0002"), None)
        # Ensure `validate_consistency()` still raises an error at this stage.
        with self.assertRaisesMessage(NodeNotFoundError, "BAD!"):
            graph.validate_consistency()
        # Remove the dummy nodes.
        graph.remove_replaced_nodes(
            replacement=("app_a", "0001_squashed_0002"),
            replaced=[("app_a", "0001"), ("app_a", "0002")],
        )
        # Ensure graph is now consistent and dependencies have been remapped
        graph.validate_consistency()
        parent_node = graph.node_map[("app_c", "0001")]
        replacement_node = graph.node_map[("app_a", "0001_squashed_0002")]
        child_node = graph.node_map[("app_b", "0001")]
        self.assertIn(parent_node, replacement_node.parents)
        self.assertIn(replacement_node, parent_node.children)
        self.assertIn(child_node, replacement_node.children)
        self.assertIn(replacement_node, child_node.parents)