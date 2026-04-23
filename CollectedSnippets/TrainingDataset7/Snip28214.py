def test_flatchoices(self):
        self.assertEqual(self.no_choices.flatchoices, [])
        self.assertEqual(self.empty_choices.flatchoices, [])
        self.assertEqual(self.empty_choices_bool.flatchoices, [])
        self.assertEqual(self.empty_choices_text.flatchoices, [])
        self.assertEqual(self.with_choices.flatchoices, [(1, "A")])
        self.assertEqual(self.with_choices_dict.flatchoices, [(1, "A")])
        self.assertEqual(self.with_choices_nested_dict.flatchoices, [(1, "A")])
        self.assertEqual(
            self.choices_from_iterator.flatchoices, [(0, "0"), (1, "1"), (2, "2")]
        )
        self.assertEqual(
            self.choices_from_callable.flatchoices, [(0, "0"), (1, "1"), (2, "2")]
        )