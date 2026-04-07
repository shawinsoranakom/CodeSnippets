def test_validate_consistency_no_error(self):
        graph = MigrationGraph()
        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_b", "0002"), None)
        graph.add_dependency(
            "app_a.0001", ("app_a", "0001"), ("app_b", "0002"), skip_validation=True
        )
        graph.validate_consistency()