def test06_expand_to_include_extent_4_tuple(self):
        """
        Testing Envelope expand_to_include -- extent as a single 4-tuple
        parameter.
        """
        self.e.expand_to_include((-1, 1, 3, 7))
        self.assertEqual((-1, 0, 5, 7), self.e)