def test_model_field_formfield_integer(self):
        model_field = pg_fields.IntegerRangeField()
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, pg_forms.IntegerRangeField)
        self.assertEqual(form_field.range_kwargs, {})