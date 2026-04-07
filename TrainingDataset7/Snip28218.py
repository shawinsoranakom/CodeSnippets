def test_choices_from_enum(self):
        # Choices class was transparently resolved when given as argument.
        self.assertEqual(self.choices_from_enum.choices, Choiceful.Suit.choices)
        self.assertEqual(self.choices_from_enum.flatchoices, Choiceful.Suit.choices)