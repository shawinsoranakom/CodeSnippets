def test05_expand_to_include_pt_2_tuple(self):
        """
        Testing Envelope expand_to_include -- point as a single 2-tuple
        parameter.
        """
        self.e.expand_to_include((10, 10))
        self.assertEqual((0, 0, 10, 10), self.e)
        self.e.expand_to_include((-10, -10))
        self.assertEqual((-10, -10, 10, 10), self.e)