def test_char_fields(self):
        self.assertEqual(
            views.get_readable_field_data_type(fields.CharField(max_length=255)),
            "String (up to 255)",
        )
        self.assertEqual(
            views.get_readable_field_data_type(fields.CharField()),
            "String (unlimited)",
        )