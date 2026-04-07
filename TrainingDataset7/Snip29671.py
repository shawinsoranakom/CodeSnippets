def test_required(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(forms.CharField(), required=True, size=3)

        data = {"array_0": "", "array_1": "", "array_2": ""}
        form = SplitForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"array": ["This field is required."]})