def test_invalid_char_length(self):
        field = SplitArrayField(forms.CharField(max_length=2), size=3)
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["abc", "c", "defg"])
        self.assertEqual(
            cm.exception.messages,
            [
                "Item 1 in the array did not validate: Ensure this value has at most 2 "
                "characters (it has 3).",
                "Item 3 in the array did not validate: Ensure this value has at most 2 "
                "characters (it has 4).",
            ],
        )