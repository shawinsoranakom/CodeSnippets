def test_repr(self):
        self.assertEqual(repr(self.node1), "<Node: (DEFAULT: ('a', 1), ('b', 2))>")
        self.assertEqual(repr(self.node2), "<Node: (DEFAULT: )>")