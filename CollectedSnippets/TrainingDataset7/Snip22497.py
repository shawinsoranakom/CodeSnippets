def test_choicefield_choices_default(self):
        f = ChoiceField()
        self.assertEqual(f.choices, [])