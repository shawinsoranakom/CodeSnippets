def test_model_field_formfield(self):
        model_field = HStoreField()
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, forms.HStoreField)