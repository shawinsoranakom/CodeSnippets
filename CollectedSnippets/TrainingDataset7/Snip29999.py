def test_model_field_formfield_datetime_default_bounds(self):
        model_field = pg_fields.DateTimeRangeField(default_bounds="[]")
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, pg_forms.DateTimeRangeField)
        self.assertEqual(form_field.range_kwargs, {"bounds": "[]"})