def test_empty_value_display_for_field(self):
        tests = [
            models.CharField(),
            models.DateField(),
            models.DecimalField(),
            models.FloatField(),
            models.URLField(),
            models.JSONField(),
            models.TimeField(),
        ]
        for model_field in tests:
            for value in model_field.empty_values:
                with self.subTest(model_field=model_field, empty_value=value):
                    display_value = display_for_field(
                        value, model_field, self.empty_value
                    )
                    self.assertEqual(display_value, self.empty_value)