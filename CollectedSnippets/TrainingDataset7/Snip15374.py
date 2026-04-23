def test_builtin_fields(self):
        self.assertEqual(
            views.get_readable_field_data_type(fields.BooleanField()),
            "Boolean (Either True or False)",
        )