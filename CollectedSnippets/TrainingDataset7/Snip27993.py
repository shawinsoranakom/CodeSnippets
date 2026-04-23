def test_formfield(self):
        model_field = models.JSONField()
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, forms.JSONField)