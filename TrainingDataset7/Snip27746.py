def test_integerchoices(self):
        self.assertEqual(
            Suit.choices, [(1, "Diamond"), (2, "Spade"), (3, "Heart"), (4, "Club")]
        )
        self.assertEqual(Suit.labels, ["Diamond", "Spade", "Heart", "Club"])
        self.assertEqual(Suit.values, [1, 2, 3, 4])
        self.assertEqual(Suit.names, ["DIAMOND", "SPADE", "HEART", "CLUB"])

        self.assertEqual(repr(Suit.DIAMOND), "Suit.DIAMOND")
        self.assertEqual(Suit.DIAMOND.label, "Diamond")
        self.assertEqual(Suit.DIAMOND.value, 1)
        self.assertEqual(Suit["DIAMOND"], Suit.DIAMOND)
        self.assertEqual(Suit(1), Suit.DIAMOND)

        self.assertIsInstance(Suit, type(models.Choices))
        self.assertIsInstance(Suit.DIAMOND, Suit)
        self.assertIsInstance(Suit.DIAMOND.label, Promise)
        self.assertIsInstance(Suit.DIAMOND.value, int)