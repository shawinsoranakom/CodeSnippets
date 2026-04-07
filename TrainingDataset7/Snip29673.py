def test_remove_trailing_nulls_not_required(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(
                forms.CharField(required=False),
                size=2,
                remove_trailing_nulls=True,
                required=False,
            )

        data = {"array_0": "", "array_1": ""}
        form = SplitForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {"array": []})