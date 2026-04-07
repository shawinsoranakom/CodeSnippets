def test_encode(self):
        for field_value in self.field_values:
            with self.subTest(field_value=field_value):
                instance = CharArrayModel(field=field_value)
                data = serializers.serialize("json", [instance])
                json_data = self.create_json_data(field_value)
                self.assertEqual(json.loads(data), json.loads(json_data))