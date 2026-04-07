def test_nullbooleanfield_4(self):
        # Make sure we're compatible with MySQL, which uses 0 and 1 for its
        # boolean values (#9609).
        NULLBOOL_CHOICES = (("1", "Yes"), ("0", "No"), ("", "Unknown"))

        class MySQLNullBooleanForm(Form):
            nullbool0 = NullBooleanField(widget=RadioSelect(choices=NULLBOOL_CHOICES))
            nullbool1 = NullBooleanField(widget=RadioSelect(choices=NULLBOOL_CHOICES))
            nullbool2 = NullBooleanField(widget=RadioSelect(choices=NULLBOOL_CHOICES))

        f = MySQLNullBooleanForm({"nullbool0": "1", "nullbool1": "0", "nullbool2": ""})
        self.assertIsNone(f.full_clean())
        self.assertTrue(f.cleaned_data["nullbool0"])
        self.assertFalse(f.cleaned_data["nullbool1"])
        self.assertIsNone(f.cleaned_data["nullbool2"])