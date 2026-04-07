def test_negation(self):
        c = Combinable()
        self.assertEqual(-c, c * -1)