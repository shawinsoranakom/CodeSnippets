def test04_expand_to_include_pt_2_params(self):
        "Testing Envelope expand_to_include -- point as two parameters."
        self.e.expand_to_include(2, 6)
        self.assertEqual((0, 0, 5, 6), self.e)
        self.e.expand_to_include(-1, -1)
        self.assertEqual((-1, -1, 5, 6), self.e)