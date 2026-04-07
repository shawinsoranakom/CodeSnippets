def test03_equivalence(self):
        "Testing Envelope equivalence."
        e1 = Envelope(0.523, 0.217, 253.23, 523.69)
        e2 = Envelope((0.523, 0.217, 253.23, 523.69))
        self.assertEqual(e1, e2)
        self.assertEqual((0.523, 0.217, 253.23, 523.69), e1)