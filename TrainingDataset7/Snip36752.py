def test_add(self):
        # start with the same children of node1 then add an item
        node3 = Node(self.node1_children)
        node3_added_child = ("c", 3)
        # add() returns the added data
        self.assertEqual(node3.add(node3_added_child, Node.default), node3_added_child)
        # we added exactly one item, len() should reflect that
        self.assertEqual(len(self.node1) + 1, len(node3))
        self.assertEqual(str(node3), "(DEFAULT: ('a', 1), ('b', 2), ('c', 3))")