def test_repr(self):
        node = IfNode(conditions_nodelists=[])
        self.assertEqual(repr(node), "<IfNode>")