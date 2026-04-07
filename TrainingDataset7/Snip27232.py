def test_validate_consistency_dummy(self):
        """
        validate_consistency() raises an error if there's an isolated dummy
        node.
        """
        msg = "app_a.0001 (req'd by app_b.0002) is missing!"
        graph = MigrationGraph()
        graph.add_dummy_node(
            key=("app_a", "0001"), origin="app_b.0002", error_message=msg
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.validate_consistency()