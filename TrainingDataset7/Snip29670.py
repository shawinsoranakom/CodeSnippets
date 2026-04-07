def test_valid(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(forms.CharField(), size=3)

        data = {"array_0": "a", "array_1": "b", "array_2": "c"}
        form = SplitForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {"array": ["a", "b", "c"]})