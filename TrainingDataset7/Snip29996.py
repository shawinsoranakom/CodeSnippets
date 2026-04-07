def test_model_field_formfield_float(self):
        model_field = pg_fields.DecimalRangeField(default_bounds="()")
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, pg_forms.DecimalRangeField)
        self.assertEqual(form_field.range_kwargs, {"bounds": "()"})