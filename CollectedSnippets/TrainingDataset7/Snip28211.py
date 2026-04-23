def test_choices(self):
        self.assertIsNone(self.no_choices.choices)
        self.assertEqual(self.empty_choices.choices, [])
        self.assertEqual(self.empty_choices_bool.choices, [])
        self.assertEqual(self.empty_choices_text.choices, [])
        self.assertEqual(self.with_choices.choices, [(1, "A")])
        self.assertEqual(self.with_choices_dict.choices, [(1, "A")])
        self.assertEqual(self.with_choices_nested_dict.choices, [("Thing", [(1, "A")])])
        self.assertEqual(
            self.choices_from_iterator.choices, [(0, "0"), (1, "1"), (2, "2")]
        )
        self.assertIsInstance(
            self.choices_from_callable.choices, CallableChoiceIterator
        )
        self.assertEqual(
            self.choices_from_callable.choices.func(), [(0, "0"), (1, "1"), (2, "2")]
        )