def test08_expand_to_include_point(self):
        "Testing Envelope expand_to_include with Point as parameter."
        self.e.expand_to_include(TestPoint(-1, 1))
        self.assertEqual((-1, 0, 5, 5), self.e)
        self.e.expand_to_include(TestPoint(10, 10))
        self.assertEqual((-1, 0, 10, 10), self.e)