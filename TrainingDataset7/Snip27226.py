def test_plan_invalid_node(self):
        """
        Tests for forwards/backwards_plan of nonexistent node.
        """
        graph = MigrationGraph()
        message = "Node ('app_b', '0001') not a valid node"

        with self.assertRaisesMessage(NodeNotFoundError, message):
            graph.forwards_plan(("app_b", "0001"))

        with self.assertRaisesMessage(NodeNotFoundError, message):
            graph.backwards_plan(("app_b", "0001"))