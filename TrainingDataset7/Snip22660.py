def test_nullbooleanfield_3(self):
        class HiddenNullBooleanForm(Form):
            hidden_nullbool1 = NullBooleanField(widget=HiddenInput, initial=True)
            hidden_nullbool2 = NullBooleanField(widget=HiddenInput, initial=False)

        f = HiddenNullBooleanForm(
            {"hidden_nullbool1": "True", "hidden_nullbool2": "False"}
        )
        self.assertIsNone(f.full_clean())
        self.assertTrue(f.cleaned_data["hidden_nullbool1"])
        self.assertFalse(f.cleaned_data["hidden_nullbool2"])