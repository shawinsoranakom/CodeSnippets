def test_add_eq_child_mixed_connector(self):
        node = Node(["a", "b"], OR)
        self.assertEqual(node.add("a", AND), "a")
        self.assertEqual(node, Node([Node(["a", "b"], OR), "a"], AND))