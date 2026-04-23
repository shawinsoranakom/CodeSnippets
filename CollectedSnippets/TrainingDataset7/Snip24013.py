def test07_expand_to_include_envelope(self):
        "Testing Envelope expand_to_include with Envelope as parameter."
        self.e.expand_to_include(Envelope(-1, 1, 3, 7))
        self.assertEqual((-1, 0, 5, 7), self.e)