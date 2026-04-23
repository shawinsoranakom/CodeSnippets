def test_create(self):
        SubNode = type("SubNode", (Node,), {})

        a = SubNode([SubNode(["a", "b"], OR), "c"], AND)
        b = SubNode.create(a.children, a.connector, a.negated)
        self.assertEqual(a, b)
        # Children lists are the same object, but equal.
        self.assertIsNot(a.children, b.children)
        self.assertEqual(a.children, b.children)
        # Child Node objects are the same objects.
        for a_child, b_child in zip(a.children, b.children):
            if isinstance(a_child, Node):
                self.assertIs(a_child, b_child)
            self.assertEqual(a_child, b_child)