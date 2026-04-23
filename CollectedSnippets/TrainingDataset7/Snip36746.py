def test_str(self):
        self.assertEqual(str(self.node1), "(DEFAULT: ('a', 1), ('b', 2))")
        self.assertEqual(str(self.node2), "(DEFAULT: )")