def test_integerchoices_containment(self):
        self.assertIn(Suit.DIAMOND, Suit)
        self.assertIn(1, Suit)
        self.assertNotIn(0, Suit)