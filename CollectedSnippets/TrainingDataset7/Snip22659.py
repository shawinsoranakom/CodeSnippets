def test_nullbooleanfield_2(self):
        # The internal value is preserved if using HiddenInput (#7753).
        class HiddenNullBooleanForm(Form):
            hidden_nullbool1 = NullBooleanField(widget=HiddenInput, initial=True)
            hidden_nullbool2 = NullBooleanField(widget=HiddenInput, initial=False)

        f = HiddenNullBooleanForm()
        self.assertHTMLEqual(
            str(f),
            '<input type="hidden" name="hidden_nullbool1" value="True" '
            'id="id_hidden_nullbool1">'
            '<input type="hidden" name="hidden_nullbool2" value="False" '
            'id="id_hidden_nullbool2">',
        )