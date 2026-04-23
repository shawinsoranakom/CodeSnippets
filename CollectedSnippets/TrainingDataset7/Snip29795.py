def test_loading(self):
        for field_value, array_field_value in self.field_values:
            with self.subTest(field_value=field_value, array_value=array_field_value):
                json_data = self.create_json_data(field_value, array_field_value)
                instance = list(serializers.deserialize("json", json_data))[0].object
                self.assertEqual(instance.field, field_value)
                self.assertEqual(instance.array_field, array_field_value)