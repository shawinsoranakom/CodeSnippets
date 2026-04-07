def test_choices_negative_index(self):
        for choices, expected_choice in [
            (self.with_choices.choices, (1, "A")),
            (self.with_choices_dict.choices, (1, "A")),
            (self.with_choices_nested_dict.choices, ("Thing", [(1, "A")])),
            (self.choices_from_iterator.choices, (2, "2")),
            (self.choices_from_callable.choices.func(), (2, "2")),
            (self.choices_from_callable.choices, (2, "2")),
        ]:
            with self.subTest(choices=choices):
                self.assertEqual(choices[-1], expected_choice)