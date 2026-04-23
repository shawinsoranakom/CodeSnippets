def test_node_str(self):
        node = Node(("app_a", "0001"))
        self.assertEqual(str(node), "('app_a', '0001')")