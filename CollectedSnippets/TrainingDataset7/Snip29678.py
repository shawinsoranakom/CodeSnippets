def test_invalid_char_length_with_remove_trailing_nulls(self):
        field = SplitArrayField(
            forms.CharField(max_length=2, required=False),
            size=3,
            remove_trailing_nulls=True,
        )
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["abc", "", ""])
        self.assertEqual(
            cm.exception.messages,
            [
                "Item 1 in the array did not validate: Ensure this value has at most 2 "
                "characters (it has 3).",
            ],
        )