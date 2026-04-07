def test_formfield(self):
        field = models.DurationField()
        self.assertIsInstance(field.formfield(), forms.DurationField)