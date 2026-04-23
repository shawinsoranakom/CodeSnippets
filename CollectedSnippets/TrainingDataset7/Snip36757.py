def test_deepcopy(self):
        a = Node([Node(["a", "b"], OR), "c"], AND)
        b = copy.deepcopy(a)
        self.assertEqual(a, b)
        # Children lists are not be the same object, but equal.
        self.assertIsNot(a.children, b.children)
        self.assertEqual(a.children, b.children)
        # Child Node objects are not be the same objects.
        for a_child, b_child in zip(a.children, b.children):
            if isinstance(a_child, Node):
                self.assertIsNot(a_child, b_child)
            self.assertEqual(a_child, b_child)