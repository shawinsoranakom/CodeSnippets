def test_validate_consistency_missing_child(self):
        graph = MigrationGraph()
        graph.add_node(("app_b", "0002"), None)
        graph.add_dependency(
            "app_b.0002", ("app_a", "0001"), ("app_b", "0002"), skip_validation=True
        )
        msg = (
            "Migration app_b.0002 dependencies reference nonexistent child node "
            "('app_a', '0001')"
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.validate_consistency()