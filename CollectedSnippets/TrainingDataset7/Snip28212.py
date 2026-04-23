def test_choices_slice(self):
        for choices, expected_slice in [
            (self.empty_choices.choices, []),
            (self.empty_choices_bool.choices, []),
            (self.empty_choices_text.choices, []),
            (self.with_choices.choices, [(1, "A")]),
            (self.with_choices_dict.choices, [(1, "A")]),
            (self.with_choices_nested_dict.choices, [("Thing", [(1, "A")])]),
            (self.choices_from_iterator.choices, [(0, "0"), (1, "1")]),
            (self.choices_from_callable.choices.func(), [(0, "0"), (1, "1")]),
            (self.choices_from_callable.choices, [(0, "0"), (1, "1")]),
        ]:
            with self.subTest(choices=choices):
                self.assertEqual(choices[:2], expected_slice)