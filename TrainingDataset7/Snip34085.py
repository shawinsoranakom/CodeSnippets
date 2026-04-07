def test_repr(self):
        node = WithNode(nodelist=[], name="a", var="dict.key")
        self.assertEqual(repr(node), "<WithNode>")