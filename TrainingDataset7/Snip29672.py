def test_remove_trailing_nulls(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(
                forms.CharField(required=False), size=5, remove_trailing_nulls=True
            )

        data = {
            "array_0": "a",
            "array_1": "",
            "array_2": "b",
            "array_3": "",
            "array_4": "",
        }
        form = SplitForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data, {"array": ["a", "", "b"]})