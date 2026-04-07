def test_validate_consistency_missing_parent(self):
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        graph.add_dependency(
            "app_a.0001", ("app_a", "0001"), ("app_b", "0002"), skip_validation=True
        )
        msg = (
            "Migration app_a.0001 dependencies reference nonexistent parent node "
            "('app_b', '0002')"
        )
        with self.assertRaisesMessage(NodeNotFoundError, msg):
            graph.validate_consistency()