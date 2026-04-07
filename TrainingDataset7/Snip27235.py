def test_infinite_loop(self):
        """
        Tests a complex dependency graph:

        app_a:        0001 <-
                             \
        app_b:        0001 <- x 0002 <-
                       /               \
        app_c:   0001<-  <------------- x 0002

        And apply squashing on app_c.
        """
        graph = MigrationGraph()

        graph.add_node(("app_a", "0001"), None)
        graph.add_node(("app_b", "0001"), None)
        graph.add_node(("app_b", "0002"), None)
        graph.add_node(("app_c", "0001_squashed_0002"), None)

        graph.add_dependency(
            "app_b.0001", ("app_b", "0001"), ("app_c", "0001_squashed_0002")
        )
        graph.add_dependency("app_b.0002", ("app_b", "0002"), ("app_a", "0001"))
        graph.add_dependency("app_b.0002", ("app_b", "0002"), ("app_b", "0001"))
        graph.add_dependency(
            "app_c.0001_squashed_0002",
            ("app_c", "0001_squashed_0002"),
            ("app_b", "0002"),
        )

        with self.assertRaises(CircularDependencyError):
            graph.ensure_not_cyclic()