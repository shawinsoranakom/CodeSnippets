def test_copy(self):
        a = Node([Node(["a", "b"], OR), "c"], AND)
        b = copy.copy(a)
        self.assertEqual(a, b)
        # Children lists are the same object.
        self.assertIs(a.children, b.children)
        # Child Node objects are the same objects.
        for a_child, b_child in zip(a.children, b.children):
            if isinstance(a_child, Node):
                self.assertIs(a_child, b_child)
            self.assertEqual(a_child, b_child)