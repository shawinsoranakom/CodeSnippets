def test_custom_fields(self):
        self.assertEqual(
            views.get_readable_field_data_type(CustomField()), "A custom field type"
        )
        self.assertEqual(
            views.get_readable_field_data_type(DescriptionLackingField()),
            "Field of type: DescriptionLackingField",
        )