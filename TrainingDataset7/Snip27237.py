def test_node_repr(self):
        node = Node(("app_a", "0001"))
        self.assertEqual(repr(node), "<Node: ('app_a', '0001')>")