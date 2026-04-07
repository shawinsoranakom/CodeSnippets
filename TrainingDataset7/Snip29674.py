def test_required_field(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(forms.CharField(), size=3)

        data = {"array_0": "a", "array_1": "b", "array_2": ""}
        form = SplitForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "array": [
                    "Item 3 in the array did not validate: This field is required."
                ]
            },
        )