def test_eq_children(self):
        node = Node(self.node1_children)
        self.assertEqual(node, self.node1)
        self.assertNotEqual(node, self.node2)