def test_field_names_should_always_be_available(self):
        for field in self.fields_and_reverse_objects:
            self.assertTrue(field.name)