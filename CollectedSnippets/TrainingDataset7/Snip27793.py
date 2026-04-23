def test_nullbooleanfield_formfield(self):
        f = models.BooleanField(null=True)
        self.assertIsInstance(f.formfield(), forms.NullBooleanField)