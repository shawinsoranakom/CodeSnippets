def test_model_field_formfield(self):
        model_field = ArrayField(models.CharField(max_length=27))
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, SimpleArrayField)
        self.assertIsInstance(form_field.base_field, forms.CharField)
        self.assertEqual(form_field.base_field.max_length, 27)