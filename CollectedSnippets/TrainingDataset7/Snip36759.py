def test_eq_connector(self):
        new_node = Node(connector="NEW")
        default_node = Node(connector="DEFAULT")
        self.assertEqual(default_node, self.node2)
        self.assertNotEqual(default_node, new_node)