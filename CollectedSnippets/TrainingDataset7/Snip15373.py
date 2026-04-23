def test_field_name(self):
        with self.assertRaises(AttributeError):
            views.get_readable_field_data_type("NotAField")